"""Isolated end-to-end import, gallery, publication and per-color cart behavior."""
import copy
import json
import tempfile
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from PIL import Image

from loja.catalog import services
from loja.catalog.publication import publish_ready_products
from loja.catalog.reference_import import prepare_catalog
from loja.media.reference_binding import bind_media
from loja.media.reference_inventory import inventory_item
from loja.media.reference_pipeline import import_inventory
from loja.tests.reference.test_import import observation


class ImportedOfferWorkflowTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "data").mkdir()
        self.path = self.root / "data/products.json"
        self.media_path = self.root / "data/media.json"
        self.catalog, _ = prepare_catalog([], [observation()])
        self.save()
        self.media_path.write_text('{"products":{}}', encoding="utf-8")
        for context in (override_settings(BASE_DIR=self.root),
                        patch("loja.catalog.repository.PRODUCTS_PATH", self.path),
                        patch("loja.media.assets.MEDIA_PATH", self.media_path)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)
        buffer = BytesIO()
        Image.new("RGB", (96, 120), "navy").save(buffer, "PNG")
        fixtures = [inventory_item(f"https://cdn.shopify.com/QA-only-{color}-{side}.png", "Montelux", color)
                    for color in ("Prata", "Preto", "Azul") for side in ("front", "side")]
        self.inventory = import_inventory(fixtures, root=self.root, fetch=lambda url: (buffer.getvalue(), "image/png"))
        self.assertEqual(len(bind_media(self.inventory)), 6)

    def save(self):
        self.path.write_text(json.dumps(self.catalog), encoding="utf-8")

    def confirm_qa_offers(self):
        # These confirmations exist only in an automatically removed test directory.
        for product in self.catalog:
            product["referencia"] = "QA-ONLY-NOT-A-MANUFACTURER-REFERENCE"
            product["identificacao"] = {"confirmada": True, "marca": "Poedagar", "modelo": "Montelux",
                "referencia": product["referencia"], "fonte": "https://qa.example.test/fixture"}
            product["variante"].update(confirmada=True, pulseira="Silicone QA")
            product["oferta_confirmada"] = True
        self.save()
        return publish_ready_products(apply=True)

    def test_downloads_alone_cannot_publish_an_unconfirmed_offer(self):
        report = publish_ready_products(apply=True)
        self.assertEqual(report["published_products"], [])
        self.assertEqual(len(report["blocked_products"]), 3)
        self.assertEqual(services.get_products(), [])

    def test_completed_variants_have_exact_galleries_zoom_and_distinct_cart_lines(self):
        self.assertEqual(self.confirm_qa_offers()["published_products"], [25, 26, 27])
        for product in services.get_products():
            self.assertEqual(len(product["images"]), 2)
            self.assertTrue(all(asset["produto_id"] == product["id"] for asset in product["images"]))
            response = self.client.get(f"/produto/{product['id']}/")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "R$ 259,00")
            self.assertContains(response, "data-gallery-index", count=2)
            self.assertContains(response, 'data-zoom="', count=2)
            self.assertEqual(len(response.context["product"]["variant_options"]), 3)
        for identity in (25, 27):
            self.assertEqual(self.client.post(f"/carrinho/adicionar/{identity}/", {"preco": "0.01"}).status_code, 302)
        cart = self.client.get("/carrinho/")
        self.assertEqual(cart.context["quantity"], 2)
        self.assertEqual(cart.context["total"], Decimal("518.00"))
        self.assertEqual({item["product"]["reference_color"] for item in cart.context["items"]}, {"Prata", "Azul"})
        self.client.post("/carrinho/remover/25/")
        self.assertEqual(self.client.get("/carrinho/").context["total"], Decimal("259.00"))

    def test_price_refresh_removes_stale_cart_offer(self):
        self.confirm_qa_offers()
        self.client.post("/carrinho/adicionar/25/")
        source = observation()
        source["price_brl"] = "269.00"
        self.catalog, _ = prepare_catalog(self.catalog, [source])
        self.save()
        response = self.client.get("/carrinho/")
        self.assertEqual(response.context["quantity"], 0)
        self.assertContains(response, "Itens antigos ou indisponíveis foram removidos")

    def test_owner_can_open_new_variant_in_management_and_native_admin(self):
        self.confirm_qa_offers()
        owner = get_user_model().objects.create_user("workflow-owner", password="test-only", is_staff=True)
        self.client.force_login(owner)
        self.assertContains(self.client.get("/gestao/catalogo/27/"), "Poedagar Montelux")
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        self.assertContains(self.client.get("/admin/catalogo-referencia/"), "Montelux")
