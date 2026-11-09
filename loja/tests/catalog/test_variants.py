"""Behavior tests with fictional supplier records; no fixture is published."""
import copy
import json
import os
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command, CommandError
from django.test import TestCase

from loja.cart import services as cart_services
from loja.catalog import services
from loja.tests.support.catalog import archived_catalog_test, legacy_catalog


@archived_catalog_test
class ConfirmedCatalogTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "products.json"
        self.products = legacy_catalog()
        identity = {"confirmada": True, "marca": "Marca QA", "modelo": "Modelo de teste",
                    "referencia": "TEST-ONLY", "fonte": "https://supplier.example.test/manual"}
        for product, color in zip(self.products[:2], ["Azul de teste", "Preto de teste"]):
            product["identificacao"] = copy.deepcopy(identity)
            product["variante"] = {"confirmada": True, "cor": color, "pulseira": "Pulseira de teste",
                                   "fonte": identity["fonte"]}
        self.save()
        self.patch = patch("loja.catalog.repository.PRODUCTS_PATH", self.path)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def save(self):
        self.path.write_text(json.dumps(self.products), encoding="utf-8")

    def test_only_same_confirmed_reference_appears_in_selector(self):
        response = self.client.get("/produto/1/")
        self.assertEqual([v["id"] for v in response.context["product"]["variant_options"]], [1, 2])
        self.assertContains(response, 'href="/produto/2/"')
        self.assertContains(response, "Azul de teste / Pulseira de teste")
        self.products[1]["identificacao"]["referencia"] = "DIFFERENT-TEST"
        self.save()
        self.assertEqual([v["id"] for v in services.get_product(1)["variant_options"]], [1])

    def test_unconfirmed_or_missing_variant_evidence_never_creates_choices(self):
        for field in ["identificacao", "variante"]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.products[1][field])
                self.products[1][field]["confirmada"] = False
                self.save()
                self.assertEqual([v["id"] for v in services.get_product(1)["variant_options"]], [1])
                self.products[1][field] = original
        self.products[1]["variante"].pop("pulseira")
        self.save()
        self.assertEqual([v["id"] for v in services.get_product(1)["variant_options"]], [1])

    def test_variant_navigation_preserves_own_price_and_cart_line(self):
        response = self.client.get("/produto/2/")
        self.assertContains(response, self.products[1]["nome"])
        self.assertContains(response, 'action="/carrinho/adicionar/2/"')
        self.assertEqual(response.context["product"]["preco"], services.get_product(2)["preco"])
        self.client.post("/carrinho/adicionar/1/")
        self.client.post("/carrinho/adicionar/2/")
        lines = cart_services.get_cart_items(self.client.session)
        self.assertEqual([(line["product"]["id"], line["quantity"]) for line in lines], [(1, 1), (2, 1)])
        self.assertNotEqual(lines[0]["unit_price"], lines[1]["unit_price"])

    def test_search_uses_confirmed_model_reference_color_and_strap(self):
        self.assertEqual({p["id"] for p in services.filter_products(query="TEST-ONLY")}, {1, 2})
        self.assertEqual([p["id"] for p in services.filter_products(query="Azul de teste")], [1])
        self.products[0]["identificacao"]["confirmada"] = False
        self.save()
        self.assertEqual(services.filter_products(query="Azul de teste"), [])

    def test_unverified_specs_and_unsafe_sources_are_not_rendered(self):
        self.products[0]["especificacoes"] = {
            "Sem comprovação": "Texto legado",
            "Pendente": {"valor": "Não publicar", "fonte": "https://supplier.example.test", "confirmada": False},
            "Insegura": {"valor": "Não publicar", "fonte": "javascript:alert(1)", "confirmada": True},
            "Verificada QA": {"valor": "Dado fictício de teste", "fonte": "https://supplier.example.test/manual", "confirmada": True},
        }
        self.save()
        self.assertEqual(services.get_product(1)["specifications"], {"Verificada QA": "Dado fictício de teste"})
        response = self.client.get("/produto/1/")
        self.assertContains(response, "Dado fictício de teste")
        self.assertNotContains(response, "Não publicar")

    def test_malformed_or_credential_source_is_rejected(self):
        for source in ["https://[", "https://user:password@example.test/manual", "http://example.test", None]:
            self.products[0]["identificacao"]["fonte"] = source
            self.save()
            self.assertIsNone(services.get_product(1)["verified_identity"])

    def test_audit_rejects_incomplete_confirmed_identity(self):
        self.products[0]["identificacao"]["referencia"] = None
        self.save()
        with self.assertRaisesMessage(CommandError, "identificacao marcada confirmada"):
            call_command("audit_storefront")

    def test_launch_section_uses_existing_launch_collection(self):
        response = self.client.get("/")
        self.assertEqual([p["id"] for p in response.context["new_products"]], [7, 9])
        self.assertContains(response, 'id="lancamentos"')

    def test_unapproved_galleries_never_create_thumbnails(self):
        response = self.client.get("/produto/1/")
        self.assertNotContains(response, "data-gallery-index")
        self.assertNotContains(response, "images.yampi.me")

    def test_gallery_thumbnails_use_only_approved_ordered_media(self):
        assets = [{"src": "img/products/qa-front.webp", "url": "/static/img/products/qa-front.webp", "alt": "Frente QA"},
                  {"src": "img/products/qa-side.webp", "url": "/static/img/products/qa-side.webp", "alt": "Lateral QA"}]
        product = services.get_product(1)
        product["images"] = assets
        product["gallery_items"] = [{"image": entry, "video": None} for entry in assets]
        with patch("loja.catalog.services.get_product", return_value=product):
            response = self.client.get("/produto/1/")
        self.assertContains(response, 'data-gallery-index="0"')
        self.assertContains(response, 'data-gallery-index="1"')
        self.assertContains(response, 'aria-current="true"')
        self.assertContains(response, 'aria-controls="product-gallery-track"', count=4)
        self.assertLess(response.content.index(b'qa-front.webp'), response.content.index(b'qa-side.webp'))


@skipUnless(os.environ.get("VRAS_BROWSER_QA") == "1", "Optional: requires isolated Chrome CDP and Node 22+")
class GalleryBrowserTests(StaticLiveServerTestCase):
    """Fixtures are temporary and approved only inside this isolated test process."""

    def test_gallery_and_confirmed_variant_in_browser(self):
        with (tempfile.TemporaryDirectory(prefix="qa-only-", dir=settings.BASE_DIR / "static/img/products") as asset_dir,
              tempfile.TemporaryDirectory() as data_dir):
            # Two solid-color PNGs test image loading; they do not depict real watches.
            def chunk(kind, content):
                return struct.pack("!I", len(content)) + kind + content + struct.pack("!I", zlib.crc32(kind + content))

            assets = []
            for name, color in [("front", b"\x44\x66\x88"), ("side", b"\x88\x66\x44")]:
                path = Path(asset_dir) / f"{name}.png"
                png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", 40, 60, 8, 2, 0, 0, 0))
                png += chunk(b"IDAT", zlib.compress((b"\0" + color * 40) * 60)) + chunk(b"IEND", b"")
                path.write_bytes(png)
                assets.append({"src": path.relative_to(settings.BASE_DIR / "static").as_posix(),
                               "alt": f"Fixture QA {name}", "origem": "Isolated test-only fixture", "autorizado": True})
            catalog = legacy_catalog()
            for product, color in zip(catalog[:2], ["Azul de teste", "Preto de teste"]):
                product["identificacao"] = {"confirmada": True, "marca": "Marca QA", "modelo": "Modelo de teste",
                                            "referencia": "TEST-ONLY", "fonte": "https://supplier.example.test/manual"}
                product["variante"] = {"confirmada": True, "cor": color, "pulseira": "Pulseira de teste",
                                       "fonte": "https://supplier.example.test/manual"}
            catalog_path = Path(data_dir) / "products.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            manifest = {"products": {"1": {"images": assets}, "2": {"images": assets[::-1]}},
                        "hero": {"image": assets[0], "mobile_image": assets[1]},
                        "editorial": {"image": assets[0]}, "campaign": {"image": assets[1]},
                        "instagram": [{"permalink": "https://www.instagram.com/p/QA-test-only/", "image": assets[0]}]}
            env = {**os.environ, "QA_BASE_URL": self.live_server_url, "QA_CONFIRMED_FIXTURE": "1"}
            with (patch("loja.catalog.repository.PRODUCTS_PATH", catalog_path), patch("loja.media.assets.load_media", return_value=manifest),
                  patch("loja.catalog.validation.publication_issues", return_value=[])):
                result = subprocess.run(["node", "scripts/browser_qa.mjs"], cwd=settings.BASE_DIR,
                                        env=env, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('"variantNavigationAndCart": "passed"', result.stdout)
