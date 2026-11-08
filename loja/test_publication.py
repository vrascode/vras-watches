"""Exercise offline import -> gated publication -> storefront/cart in isolation."""
import copy
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from PIL import Image

from loja import services

ROOT = Path(__file__).resolve().parent.parent


class PublicationWorkflowTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "data").mkdir()
        (self.root / "static").mkdir()
        self.source = self.root / "originals"
        self.source.mkdir()
        self.path = self.root / "data/products.json"
        self.media_path = self.root / "data/media.json"
        self.catalog = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))
        self.save_catalog()
        self.media_path.write_text('{"products": {}}\n', encoding="utf-8")
        for context in (override_settings(BASE_DIR=self.root),
                        patch("loja.services.PRODUCTS_PATH", self.path),
                        patch("loja.media.MEDIA_PATH", self.media_path)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def save_catalog(self):
        self.path.write_text(json.dumps(self.catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def execute(self, apply=False):
        output = StringIO()
        call_command("publish_ready_products", apply=apply, stdout=output)
        return json.loads(output.getvalue())

    def import_fixture(self, variant_id=None):
        """A solid test block, never a photograph or a production confirmation."""
        product = self.catalog[0]
        Image.new("RGB", (30, 40), "gray").save(self.source / "test-only.png")
        manifest = {"assets": [{
            "id": "qa-only", "arquivo": "test-only.png", "tipo": "image", "destino": "product",
            "produto_id": product["id"], "variante_fonte_id": variant_id or product["variantes_fonte"][0]["source_sku_id"],
            "produto_confirmado": True, "autorizado": True, "origem": "Isolated QA color block",
            "comprovante": "Test fixture only, not a commercial photo", "alt": "QA color block",
        }]}
        (self.source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        call_command("import_store_media", source=str(self.source), apply=True, stdout=StringIO())

    def confirm_fixture(self):
        product = self.catalog[0]
        product["referencia"] = "QA-ONLY"
        product["identificacao"] = {
            "confirmada": True, "marca": product["marca"], "modelo": product["modelo"],
            "referencia": "QA-ONLY", "fonte": "https://supplier.example.test/qa-only",
        }
        product["variante"] = {
            "confirmada": True, "cor": "QA color", "pulseira": "QA strap",
            "fonte": "https://supplier.example.test/qa-only",
            "source_variant_id": product["variantes_fonte"][0]["source_sku_id"],
        }
        product["oferta_confirmada"] = True
        self.save_catalog()

    def test_current_incomplete_offers_stay_drafts_without_any_file_changes(self):
        before = (self.path.read_bytes(), self.media_path.read_bytes())
        result = self.execute(apply=True)
        self.assertFalse(result["changed"])
        self.assertEqual(result["published_products"], [])
        self.assertEqual(len(result["blocked_products"]), 12)
        for item in result["blocked_products"]:
            self.assertEqual(set(item["issues"]), {
                "referencia_do_fabricante_nao_confirmada", "variante_nao_confirmada",
                "fotografia_autorizada_do_sku_pendente", "oferta_vras_nao_confirmada",
            })
        self.assertEqual((self.path.read_bytes(), self.media_path.read_bytes()), before)

    def test_authorized_import_never_supplies_identity_variant_or_inventory(self):
        original = self.path.read_bytes()
        self.import_fixture()
        self.assertTrue(list((self.root / "static/img/products/poedagar/army").glob("*.webp")))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.execute(apply=True)["ready_products"], [])
        self.assertEqual(services.get_products(), [])

    def test_dry_run_does_not_publish_ready_offer(self):
        self.import_fixture()
        self.confirm_fixture()
        before = self.path.read_bytes()
        result = self.execute()
        self.assertEqual(result["ready_products"], [13])
        self.assertEqual(result["published_products"], [])
        self.assertFalse(result["changed"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_publish_changes_only_status_and_is_idempotent(self):
        self.import_fixture()
        self.confirm_fixture()
        before = copy.deepcopy(self.catalog)
        before_media = self.media_path.read_bytes()
        result = self.execute(apply=True)
        self.assertEqual(result["published_products"], [13])
        before[0]["status"] = "publicado"
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), before)
        self.assertEqual(self.media_path.read_bytes(), before_media)
        published = self.path.read_bytes()
        repeated = self.execute(apply=True)
        self.assertFalse(repeated["changed"])
        self.assertEqual(repeated["already_published"], [13])
        self.assertEqual(self.path.read_bytes(), published)

    def test_wrong_variant_photo_and_unapproved_price_each_block_publication(self):
        self.confirm_fixture()
        self.import_fixture(self.catalog[0]["variantes_fonte"][1]["source_sku_id"])
        result = self.execute(apply=True)
        self.assertIn("fotografia_autorizada_do_sku_pendente", result["blocked_products"][0]["issues"])
        self.assertEqual(result["published_products"], [])
        self.import_fixture()
        self.catalog[0]["preco"] = 0.01
        self.save_catalog()
        result = self.execute(apply=True)
        self.assertIn("preco_sem_aprovacao_correspondente", result["blocked_products"][0]["issues"])
        self.assertEqual(result["published_products"], [])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))[0]["preco"], 0.01)

    def test_missing_vras_availability_blocks_even_with_authorized_matching_photo(self):
        self.import_fixture()
        self.confirm_fixture()
        self.catalog[0]["oferta_confirmada"] = False
        self.save_catalog()
        result = self.execute(apply=True)
        self.assertEqual(result["blocked_products"][0]["issues"], ["oferta_vras_nao_confirmada"])
        self.assertEqual(result["published_products"], [])

    def test_duplicate_ids_abort_without_writing(self):
        self.catalog[1]["id"] = self.catalog[0]["id"]
        self.save_catalog()
        before = self.path.read_bytes()
        with self.assertRaisesMessage(CommandError, "IDs inválidos ou duplicados"):
            self.execute(apply=True)
        self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_catalog_or_media_edits_abort_without_overwriting(self):
        self.import_fixture()
        self.confirm_fixture()
        hydrate = services.get_products
        for target in (self.path, self.media_path):
            with self.subTest(target=target.name):
                def edited_catalog(*args, **kwargs):
                    products = hydrate(*args, **kwargs)
                    target.write_bytes(target.read_bytes() + b"\n")
                    return products
                with patch("loja.services.get_products", side_effect=edited_catalog):
                    with self.assertRaisesMessage(CommandError, "mudaram durante a validação"):
                        self.execute(apply=True)
                self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))[0]["status"], "rascunho")
                self.assertFalse(list(self.path.parent.glob(".publish-*.tmp")))

    def test_published_offer_uses_approved_cents_and_unavailable_offer_leaves_cart(self):
        self.import_fixture()
        self.confirm_fixture()
        self.execute(apply=True)
        self.assertEqual(self.client.get("/produto/13/").status_code, 200)
        self.assertContains(self.client.get("/produtos/"), "R$ 196,92")
        self.assertEqual(self.client.get("/produto/14/").status_code, 404)
        response = self.client.post("/carrinho/atualizar/13/", {"quantity": 3, "preco": "0.01"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(services.cart_summary(self.client.session)["total"], Decimal("590.76"))
        self.assertContains(self.client.get("/carrinho/"), "R$ 590,76")
        self.catalog = json.loads(self.path.read_text(encoding="utf-8"))
        self.catalog[0]["oferta_confirmada"] = False
        self.save_catalog()
        self.assertEqual(self.client.post("/carrinho/adicionar/13/").status_code, 404)
        self.assertEqual(services.cart_summary(self.client.session)["items"], [])
