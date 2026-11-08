"""Approved-price tests use current evidence; physical inventory is never guessed."""
import base64
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import re
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from loja import services
from loja.pricing import price_update

ROOT = Path(__file__).resolve().parent.parent
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=")


def inputs():
    return (json.loads((ROOT / "data/products.json").read_text(encoding="utf-8")),
            json.loads((ROOT / "data/poedagar_price_verification.json").read_text(encoding="utf-8")))


class ApprovedPriceDataTests(SimpleTestCase):
    def test_twelve_selling_prices_match_current_unit_evidence_and_not_pix(self):
        catalog, evidence = inputs()
        observed = {p["product_id"]: p for p in evidence["products"]}
        self.assertEqual(len(catalog), 12)
        for product in catalog:
            source = observed[product["id"]]
            with self.subTest(model=product["modelo"]):
                self.assertEqual(source["model"], product["modelo"])
                self.assertEqual(source["url"], product["fontes"]["url_modelo_e_preco"])
                self.assertTrue(source["verified"])
                self.assertTrue(services.approved_price(product))
                self.assertTrue(product["aprovacao_preco"]["registro"])
                self.assertFalse(any("aprovação de preço" in text.casefold() for text in product["pendencias"]))
                for variant in source["variants"]:
                    self.assertEqual(Decimal(str(product["preco"])), Decimal(variant["unit_price_brl"]))
                    self.assertEqual(variant["unit_price_brl"], variant["billet_price_brl"])
                    self.assertNotEqual(Decimal(str(product["preco"])), Decimal(variant["pix_price_brl"]))

    def test_each_of_the_57_source_variants_has_its_own_price_approval(self):
        catalog, _ = inputs()
        total = 0
        for product in catalog:
            approvals = product["aprovacao_preco"]["variantes"]
            self.assertEqual(set(approvals), {str(v["source_sku_id"]) for v in product["variantes_fonte"]})
            for variant in product["variantes_fonte"]:
                selected = copy.deepcopy(product)
                selected["variante"] = {"source_variant_id": variant["source_sku_id"]}
                self.assertTrue(services.approved_price(selected))
                total += 1
            selected["variante"]["source_variant_id"] = -1
            self.assertFalse(services.approved_price(selected))
        self.assertEqual(total, 57)

    def test_price_update_preserves_physical_identity_media_and_availability(self):
        catalog, report = inputs()
        product = catalog[0]
        updated = price_update(product, report["products"][0], "Test-only explicit authorization", "2026-11-07")
        for field in ["identificacao", "referencia", "variante", "oferta_confirmada", "galeria", "videos", "status"]:
            self.assertEqual(updated[field], product[field])

    def test_wrong_model_variant_title_and_conditional_prices_are_rejected(self):
        catalog, report = inputs()
        source = report["products"][0]
        for alteration in ["model", "variant", "pix", "quantity"]:
            with self.subTest(alteration=alteration):
                bad = copy.deepcopy(source)
                if alteration == "model":
                    bad["model"] = "Other model"
                elif alteration == "variant":
                    bad["variants"][0]["title"] = "Other color"
                elif alteration == "pix":
                    bad["variants"][0]["unit_price_brl"] = bad["variants"][0]["pix_price_brl"]
                else:
                    bad["condition_review"]["coupon_or_minimum_quantity_used"] = True
                with self.assertRaises(ValueError):
                    price_update(catalog[0], bad, "Test-only authorization", "2026-11-07")

    def test_different_variant_prices_are_not_collapsed_to_an_arbitrary_model_price(self):
        catalog, report = inputs()
        bad = copy.deepcopy(report["products"][0])
        bad["variants"][0]["unit_price_brl"] = "210.00"
        bad["variants"][0]["billet_price_brl"] = "210.00"
        with self.assertRaisesMessage(ValueError, "preços distintos"):
            price_update(catalog[0], bad, "Test-only authorization", "2026-11-07")

    def test_approval_for_unselected_variant_cannot_be_a_null_id_loophole(self):
        product = inputs()[0][0]
        product["aprovacao_preco"].pop("variantes")
        product["aprovacao_preco"]["source_variant_id"] = None
        product["variante"] = None
        self.assertFalse(services.approved_price(product))


def ready_fixture(product, source_variant_id):
    """Fictional physical confirmation only inside isolated tests."""
    product.update(status="publicado", oferta_confirmada=True, referencia=f"QA-{product['id']}-ONLY")
    product["identificacao"] = {"confirmada": True, "marca": product["marca"], "modelo": product["modelo"],
                                 "referencia": product["referencia"], "fonte": "https://supplier.example.test/qa-only"}
    product["variante"] = {"confirmada": True, "cor": "Cor QA", "pulseira": "Pulseira QA",
                            "source_variant_id": source_variant_id, "fonte": "https://supplier.example.test/qa-only"}


class ApprovedPriceDisplayTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "products.json"
        self.images = tempfile.TemporaryDirectory(prefix="qa-prices-", dir=ROOT / "static/img/products")
        self.addCleanup(self.images.cleanup)
        photo = Path(self.images.name) / "fixture.png"
        photo.write_bytes(PNG)
        self.catalog, report = inputs()
        self.evidence = {p["product_id"]: p for p in report["products"]}
        manifest = {"products": {}}
        for product in self.catalog:
            variant_id = next(v["source_sku_id"] for v in product["variantes_fonte"] if v["source_stock_status"] == "in_stock")
            ready_fixture(product, variant_id)
            manifest["products"][str(product["id"])] = {"images": [{
                "src": photo.relative_to(ROOT / "static").as_posix(), "origem": "Test-only image", "autorizado": True,
                "produto_id": product["id"], "modelo": product["modelo"], "catalog_generation": "poedagar-v1",
                "source_variant_id": variant_id, "alt": "Test-only color block"}]}
        self.path.write_text(json.dumps(self.catalog), encoding="utf-8")
        for mock in [patch("loja.services.PRODUCTS_PATH", self.path), patch("loja.media.load_media", return_value=manifest)]:
            mock.start()
            self.addCleanup(mock.stop)

    def test_cards_and_details_show_exact_approved_prices_for_all_models(self):
        response = self.client.get("/produtos/")
        self.assertEqual(len(response.context["products"]), 12)
        cards = re.findall(r'<article class="product-card".*?</article>', response.content.decode(), re.S)
        for product in self.catalog:
            expected = services.format_brl(self.evidence[product["id"]]["variants"][0]["unit_price_brl"])
            card = next(card for card in cards if f'href="/produto/{product["id"]}/"' in card)
            self.assertIn(expected, card)
            self.assertContains(self.client.get(f'/produto/{product["id"]}/'), f'<p class="detail-price">{expected}</p>', html=True)

    def test_cart_subtotals_use_verified_cents_and_ignore_browser_price(self):
        expected = Decimal("0.00")
        for index, product in enumerate(self.catalog, 1):
            quantity = index % 3 + 1
            response = self.client.post(f'/carrinho/atualizar/{product["id"]}/', {"quantity": quantity, "preco": "0.01"})
            self.assertEqual(response.status_code, 302)
            expected += Decimal(self.evidence[product["id"]]["variants"][0]["unit_price_brl"]) * quantity
        summary = services.cart_summary(self.client.session)
        self.assertEqual(summary["total"], expected)
        for item in summary["items"]:
            unit = Decimal(self.evidence[item["product"]["id"]]["variants"][0]["unit_price_brl"])
            self.assertEqual(item["unit_price"], unit)
            self.assertEqual(item["subtotal"], unit * item["quantity"])


class PriceApplicationCommandTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "data").mkdir()
        (self.root / "static").mkdir()
        self.catalog, self.report = inputs()
        self.report["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
        for product in self.catalog:
            product["preco"] = None
            product["aprovacao_preco"] = {"aprovado": False}
        self.path = self.root / "data/products.json"
        self.path.write_text(json.dumps(self.catalog), encoding="utf-8")
        self.report_path = self.root / "data/poedagar_price_verification.json"
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")

    def execute(self, apply=False, manifest=None):
        with (override_settings(BASE_DIR=self.root), patch("loja.services.PRODUCTS_PATH", self.path),
              patch("loja.media.load_media", return_value=manifest or {})):
            output = StringIO()
            call_command("apply_reference_prices", approval_record="Test-only explicit approval", apply=apply, stdout=output)
            return json.loads(output.getvalue())

    def test_dry_run_preserves_catalog(self):
        original = self.path.read_bytes()
        self.assertEqual(self.execute()["updated_prices"], 12)
        self.assertEqual(self.path.read_bytes(), original)

    def test_apply_updates_prices_but_does_not_publish_incomplete_offers(self):
        result = self.execute(apply=True)
        self.assertEqual(result["published_products"], [])
        updated = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertTrue(all(p["preco"] is not None and p["status"] == "rascunho" for p in updated))

    def test_unconfirmed_price_stays_unpriced_and_other_models_update(self):
        self.report["products"][0]["verified"] = False
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        result = self.execute(apply=True)
        self.assertEqual(result["updated_prices"], 11)
        self.assertIsNone(json.loads(self.path.read_text(encoding="utf-8"))[0]["preco"])

    def test_old_snapshot_cannot_be_applied_as_current_price(self):
        self.report["checked_at_utc"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        original = self.path.read_bytes()
        with self.assertRaisesMessage(CommandError, "Refaça"):
            self.execute(apply=True)
        self.assertEqual(self.path.read_bytes(), original)

    def test_only_offer_with_all_other_requirements_can_publish_after_price_approval(self):
        product = self.catalog[0]
        variant_id = product["variantes_fonte"][0]["source_sku_id"]
        ready_fixture(product, variant_id)
        product["status"] = "rascunho"
        self.path.write_text(json.dumps(self.catalog), encoding="utf-8")
        (self.root / "static/fixture.png").write_bytes(PNG)
        asset = {"src": "fixture.png", "origem": "Test-only fixture", "autorizado": True,
                 "produto_id": product["id"], "modelo": product["modelo"], "catalog_generation": "poedagar-v1",
                 "source_variant_id": variant_id}
        result = self.execute(apply=True, manifest={"products": {str(product["id"]): {"images": [asset]}}})
        self.assertEqual(result["published_products"], [product["id"]])
