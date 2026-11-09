"""Real receipt/import/publication flow against isolated files and fictional attestations."""
import json
import tempfile
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from PIL import Image

from loja.cart import services as cart_services
from loja.catalog import services
from loja.management_portal.services import catalog_version


ROOT = Path(__file__).resolve().parents[3]


class ReceiptWorkspace:
    def prepare_workspace(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "data").mkdir()
        (self.root / "static").mkdir()
        self.catalog = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))
        self.path = self.root / "data/products.json"
        self.path.write_text(json.dumps(self.catalog), encoding="utf-8")
        self.media_path = self.root / "data/media.json"
        self.media_path.write_text('{"products": {}}', encoding="utf-8")
        for context in (override_settings(BASE_DIR=self.root, STATICFILES_DIRS=[self.root / "static"]),
                        patch("loja.catalog.repository.PRODUCTS_PATH", self.path), patch("loja.media.assets.MEDIA_PATH", self.media_path)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)
        self.owner = get_user_model().objects.create_user("qa-owner", password="QA-only-owner-password", is_staff=True)

    def photo(self, filename="test-only.png", color="gray"):
        buffer = BytesIO()
        Image.new("RGB", (900, 1200), color).save(buffer, "PNG")
        return SimpleUploadedFile(filename, buffer.getvalue(), content_type="image/png")

    def fields(self, **changes):
        fields = {
            "catalog_version": catalog_version(), "referencia": "QA-ONLY-NOT-A-REAL-SKU",
            "fonte": "https://supplier.example.test/qa-only", "identidade_confirmada": "on",
            "variante": self.catalog[0]["variantes_fonte"][0]["source_sku_id"], "cor_caixa": "QA case",
            "cor_mostrador": "QA dial", "cor_pulseira": "QA strap color", "tipo_pulseira": "QA strap type",
            "variante_confirmada": "on", "oferta_confirmada": "on", "registro_oferta": "Isolated QA availability only",
            "acao_galeria": "append", "origem": "Isolated solid color QA block", "comprovante": "QA fixture only",
            "fotos_autorizadas": "on", "fotos": [self.photo()],
        }
        fields.update(changes)
        return fields


class CatalogReceiptTests(ReceiptWorkspace, TestCase):
    def setUp(self):
        self.prepare_workspace()
        self.client.force_login(self.owner)

    def test_guests_nonstaff_and_missing_csrf_cannot_change_catalog(self):
        before = (self.path.read_bytes(), self.media_path.read_bytes())
        guest = Client()
        response = guest.post("/gestao/catalogo/13/", self.fields())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/gestao/entrar/", response.url)
        user = get_user_model().objects.create_user("ordinary-user", password="QA-only-user")
        guest.force_login(user)
        self.assertEqual(guest.get("/gestao/catalogo/").status_code, 302)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        self.assertEqual(csrf_client.post("/gestao/catalogo/13/", self.fields()).status_code, 403)
        self.assertEqual((self.path.read_bytes(), self.media_path.read_bytes()), before)

    def test_dashboard_is_private_noindex_and_does_not_select_a_variant(self):
        response = self.client.get("/gestao/catalogo/")
        self.assertContains(response, 'name="robots" content="noindex,nofollow"')
        self.assertEqual(len(response.context["products"]), 12)
        self.assertIn("no-store", response.headers["Cache-Control"])
        response = self.client.get("/gestao/catalogo/13/")
        self.assertIsNone(response.context["form"].initial["variante"])
        self.assertFalse(response.context["form"].initial["identidade_confirmada"])
        self.assertFalse(response.context["form"].initial["oferta_confirmada"])

    def test_full_owner_submission_imports_responsive_gallery_and_publishes_without_repricing(self):
        before = json.loads(self.path.read_text(encoding="utf-8"))
        response = self.client.post("/gestao/catalogo/13/", self.fields(usar_banner="on", fotos=[self.photo(), self.photo("side.png", "navy")]))
        self.assertRedirects(response, "/gestao/catalogo/13/")
        products = services.get_products()
        self.assertEqual([p["id"] for p in products], [13])
        product = products[0]
        self.assertEqual(product["publication_issues"], [])
        self.assertEqual(len(product["images"]), 2)
        self.assertTrue(product["cover"]["srcset"])
        self.assertEqual((product["cover"]["width"], product["cover"]["height"]), (900, 1200))
        self.assertTrue(all(a["src"].endswith(".webp") and a["produto_id"] == 13 for a in product["images"]))
        after = json.loads(self.path.read_text(encoding="utf-8"))
        for old, new in zip(before, after):
            self.assertEqual(old["preco"], new["preco"])
            self.assertEqual(old["aprovacao_preco"], new["aprovacao_preco"])
        self.assertEqual(after[1:], before[1:])
        receipt_dir = next((self.root / "midias-instagram/recebidos").iterdir())
        receipt = json.loads((receipt_dir / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["actor"], "qa-owner")
        self.assertEqual(receipt["status"], "applied")
        self.assertEqual(json.loads((receipt_dir / "before-products.json").read_text(encoding="utf-8")), before)
        self.assertTrue((receipt_dir / "original-1.png").exists())
        self.assertContains(self.client.get("/"), "R$ 196,92")
        self.assertContains(self.client.get("/produto/13/"), "QA case")
        self.client.post("/carrinho/atualizar/13/", {"quantity": 3, "preco": "0.01"})
        self.assertEqual(cart_services.cart_summary(self.client.session)["total"], Decimal("590.76"))

    def test_photos_without_rights_or_variant_confirmation_are_rejected_with_no_writes(self):
        before = (self.path.read_bytes(), self.media_path.read_bytes())
        for field in ("fotos_autorizadas", "variante_confirmada", "comprovante", "identidade_confirmada", "referencia"):
            with self.subTest(field=field):
                response = self.client.post("/gestao/catalogo/13/", self.fields(**{field: ""}))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual((self.path.read_bytes(), self.media_path.read_bytes()), before)
        self.assertFalse((self.root / "midias-instagram").exists())

    def test_foreign_variant_and_disguised_image_are_rejected(self):
        before = self.path.read_bytes()
        foreign = self.catalog[1]["variantes_fonte"][0]["source_sku_id"]
        response = self.client.post("/gestao/catalogo/13/", self.fields(variante=foreign))
        self.assertIn("variante", response.context["form"].errors)
        bad = SimpleUploadedFile("photo.png", b"<script>alert(1)</script>", content_type="image/png")
        response = self.client.post("/gestao/catalogo/13/", self.fields(fotos=[bad]))
        self.assertIn("fotos", response.context["form"].errors)
        self.assertEqual(self.path.read_bytes(), before)

    def test_complete_photos_without_offer_stay_draft_then_metadata_only_save_publishes(self):
        response = self.client.post("/gestao/catalogo/13/", self.fields(oferta_confirmada=""))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(services.get_products(), [])
        self.assertEqual(len(services.get_products(include_drafts=True)[0]["images"]), 1)
        self.assertEqual(self.client.get("/produto/13/").status_code, 404)
        response = self.client.post("/gestao/catalogo/13/", self.fields(fotos=[]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual([p["id"] for p in services.get_products()], [13])

    def test_availability_can_be_withdrawn_and_existing_cart_is_pruned(self):
        self.client.post("/gestao/catalogo/13/", self.fields())
        self.client.post("/carrinho/adicionar/13/")
        self.assertEqual(cart_services.cart_count(self.client.session), 1)
        self.client.post("/gestao/catalogo/13/", self.fields(fotos=[], oferta_confirmada=""))
        self.assertEqual(services.get_products(), [])
        self.assertEqual(cart_services.get_cart(self.client.session), {})
        self.assertEqual(self.client.post("/carrinho/adicionar/13/").status_code, 404)

    def test_variant_replacement_never_reuses_old_photo_or_old_cart_line(self):
        self.client.post("/gestao/catalogo/13/", self.fields())
        self.client.post("/carrinho/adicionar/13/")
        second = self.catalog[0]["variantes_fonte"][1]["source_sku_id"]
        # Keeping the old gallery while changing variant must not produce a sale.
        self.client.post("/gestao/catalogo/13/", self.fields(variante=second, fotos=[]))
        self.assertEqual(services.get_products(), [])
        # Explicit replacement imports a new corresponding photo and can publish.
        self.client.post("/gestao/catalogo/13/", self.fields(variante=second, acao_galeria="replace"))
        product = services.get_products()[0]
        self.assertTrue(all(a["source_variant_id"] == second for a in product["images"]))
        self.assertEqual(cart_services.get_cart(self.client.session), {})

    def test_partial_identity_save_never_confirms_fields_or_publishes(self):
        response = self.client.post("/gestao/catalogo/13/", {
            "catalog_version": catalog_version(), "acao_galeria": "append", "referencia": "QA unconfirmed",
        })
        self.assertEqual(response.status_code, 302)
        product = services.get_products(include_drafts=True)[0]
        self.assertFalse(product["oferta_confirmada"])
        self.assertIsNone(product["verified_identity"])
        self.assertIsNone(product["verified_variant"])
        self.assertFalse(product["can_purchase"])

    def test_adding_photos_of_same_offer_preserves_valid_cart_line(self):
        self.client.post("/gestao/catalogo/13/", self.fields())
        self.client.post("/carrinho/adicionar/13/")
        revision = services.get_products()[0]["oferta_revisao"]
        self.client.post("/gestao/catalogo/13/", self.fields(fotos=[self.photo("side.png", "navy")]))
        self.assertEqual(services.get_products()[0]["oferta_revisao"], revision)
        self.assertEqual(cart_services.get_cart(self.client.session), {"13": 1})

    def test_stale_submission_and_parallel_lock_do_not_overwrite_changes(self):
        fields = self.fields()
        self.path.write_bytes(self.path.read_bytes() + b"\n")
        before = self.path.read_bytes()
        response = self.client.post("/gestao/catalogo/13/", fields)
        self.assertContains(response, "O catálogo mudou")
        self.assertEqual(self.path.read_bytes(), before)
        lock = self.path.parent / ".owner-intake.lock"
        lock.touch()
        response = self.client.post("/gestao/catalogo/13/", self.fields())
        self.assertContains(response, "Outro recebimento")
        self.assertEqual(self.path.read_bytes(), before)
