"""Business tests for additive reference imports, source prices and duplicates."""
import copy
import json
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings

from loja.catalog import pricing
from loja.catalog.reference_import import prepare_catalog, import_observations
from loja.catalog.reference_schema import validate_observation
from loja.catalog.reference_storage import atomic_write, catalog_lock


ROOT = settings.BASE_DIR


def observation():
    return copy.deepcopy(json.loads((ROOT / "data/reference_catalog.json").read_text(encoding="utf-8"))["products"][0])


class ReferenceImportTests(SimpleTestCase):
    def test_montelux_price_and_exact_colors(self):
        products, report = prepare_catalog([], [observation()])
        self.assertEqual(report["created"], [25, 26, 27])
        self.assertEqual({p["reference_color"] for p in products}, {"Prata", "Preto", "Azul"})
        for product in products:
            self.assertEqual(Decimal(str(product["preco"])), Decimal("259.00"))
            self.assertTrue(pricing.approved_price(product))
            self.assertEqual(product["marca"], "Poedagar")
            self.assertIsNone(product["referencia"])
            self.assertFalse(product["oferta_confirmada"])
            self.assertEqual(product["status"], "rascunho")
            self.assertEqual(product["source_id_kind"], "derived_observation_id")

    def test_existing_catalog_unchanged_and_reimport_has_no_duplicates(self):
        existing = [{"id": 13, "nome": "Keep this", "preco": 42}]
        first, _ = prepare_catalog(existing, [observation()])
        second, report = prepare_catalog(first, [observation()])
        self.assertEqual(first, second)
        self.assertEqual(second[0], existing[0])
        self.assertEqual(report["created"], [])
        self.assertEqual(report["updated"], [25, 26, 27])

    def test_prices_are_per_variant_and_not_pix(self):
        source = observation()
        source["variants"][1]["price_brl"] = "279.90"
        source["pix_price"] = "0.01"
        products, _ = prepare_catalog([], [source])
        self.assertEqual([p["preco"] for p in products], [259.0, 279.9, 259.0])

    def test_price_change_invalidates_previous_cart_revision(self):
        products, _ = prepare_catalog([], [observation()])
        source = observation()
        source["price_brl"] = "269.00"
        changed, _ = prepare_catalog(products, [source])
        self.assertTrue(changed[0]["oferta_revisao"])
        self.assertTrue(pricing.approved_price(changed[0]))

    def test_platform_id_refresh_withdraws_stale_variant_confirmation(self):
        products, _ = prepare_catalog([], [observation()])
        products[0].update(status="publicado")
        products[0]["variante"]["confirmada"] = True
        source = observation()
        source["variants"][0]["source_id"] = 987654321
        changed, _ = prepare_catalog(products, [source])
        self.assertEqual(changed[0]["status"], "rascunho")
        self.assertFalse(changed[0]["variante"]["confirmada"])
        self.assertEqual(changed[0]["source_id_kind"], "platform_variant")

    def test_invalid_prices_variants_brand_and_sources_rejected(self):
        for field, value in [("price_brl", "NaN"), ("price_brl", "-1"), ("price_brl", "1.001"),
                             ("brand", "VRAS"), ("url", "https://evil.example/products/watch"),
                             ("variants", []), ("variants", [{"title": "Prata"}, {"title": "prata"}])]:
            source = observation()
            source[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_observation(source)

    def test_duplicate_batch_and_duplicate_existing_ids_rejected(self):
        with self.assertRaises(ValueError):
            prepare_catalog([], [observation(), observation()])
        with self.assertRaises(ValueError):
            prepare_catalog([{"id": 13}, {"id": 13}], [observation()])

    def test_dry_run_apply_and_lock_preserve_unrelated_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            path = root / "data/products.json"
            before = b'[{"id":13,"nome":"Preserve"}]'
            path.write_bytes(before)
            with override_settings(BASE_DIR=root), patch("loja.catalog.repository.PRODUCTS_PATH", path):
                self.assertFalse(import_observations([observation()])["applied"])
                self.assertEqual(path.read_bytes(), before)
                with catalog_lock(), self.assertRaisesMessage(ValueError, "andamento"):
                    import_observations([observation()], apply=True)
                self.assertTrue(import_observations([observation()], apply=True)["applied"])
                self.assertEqual(len(json.loads(path.read_bytes())), 4)

    def test_optimistic_write_rejects_changed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_bytes(b"newer")
            with self.assertRaises(ValueError):
                atomic_write(path, b"replace", expected=b"stale")
            self.assertEqual(path.read_bytes(), b"newer")
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_download_requires_apply(self):
        with self.assertRaisesMessage(CommandError, "exige --apply"):
            call_command("import_reference_catalog", download_media=True, stdout=StringIO())
