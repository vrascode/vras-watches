"""Availability, color routing, catalog provenance and admin permissions."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from loja.catalog.presentation import reference_cards, related_models
from loja.catalog import services


class ReferencePageTests(TestCase):
    def test_montelux_has_brand_price_specs_and_three_variant_urls(self):
        response = self.client.get("/colecao/montelux/")
        self.assertEqual(response.status_code, 200)
        for text in ("Poedagar Montelux", "R$ 259,00", "42 mm", "12 mm", "88 g", "Hardlex", "3 ATM"):
            self.assertContains(response, text)
        product = response.context["product"]
        self.assertEqual(len(product["variant_options"]), 3)
        self.assertEqual(product["selected_color"], "Prata")
        self.assertNotContains(response, "data-add-cart")
        self.assertContains(response, "Disponibilidade em breve")
        self.assertContains(response, 'content="noindex,follow"')

    def test_color_selection_changes_exact_product_id_and_link_selection(self):
        first = self.client.get("/colecao/montelux/").context["product"]
        response = self.client.get("/colecao/montelux/?cor=Azul")
        selected = response.context["product"]
        self.assertNotEqual(first["id"], selected["id"])
        self.assertEqual(selected["selected_color"], "Azul")
        self.assertEqual([v["label"] for v in selected["variant_options"] if v["selected"]], ["Azul"])
        self.assertEqual(selected["preco"], Decimal("259.0"))

    def test_catalog_title_contains_only_title_text(self):
        response = self.client.get("/produtos/")
        title = response.content.decode().split("<title>", 1)[1].split("</title>", 1)[0]
        self.assertNotIn("<", title)
        self.assertIn("VRAS Watches", title)

    def test_unknown_model_404_and_unknown_color_defaults_safely(self):
        self.assertEqual(self.client.get("/colecao/does-not-exist/").status_code, 404)
        response = self.client.get("/colecao/montelux/?cor=<script>alert(1)</script>")
        self.assertEqual(response.context["product"]["selected_color"], "Prata")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_reference_offers_cannot_be_added_until_complete(self):
        for product in services.get_products(include_drafts=True):
            if product.get("reference_import"):
                self.assertEqual(self.client.post(f"/carrinho/adicionar/{product['id']}/").status_code, 404)

    def test_catalog_counts_reference_models_without_false_empty_message(self):
        response = self.client.get("/produtos/?q=Montelux")
        self.assertEqual(response.context["product_count"], 1)
        self.assertContains(response, "Poedagar Montelux")
        self.assertNotContains(response, 'class="empty-state"')

    def test_reference_cards_group_colors_and_respect_filters(self):
        self.assertEqual(len(reference_cards(query="Montelux")), 1)
        self.assertEqual(reference_cards(query="Montelux")[0]["color_count"], 3)
        self.assertEqual(reference_cards(category="Unknown"), [])
        prices = [p["preco"] for p in reference_cards(sort="preco_asc")]
        self.assertEqual(prices, sorted(prices))

    def test_related_excludes_other_colors_of_same_model(self):
        products = services.get_products(include_drafts=True)
        montelux = next(p for p in products if p.get("modelo") == "Montelux")
        related = related_models(montelux, products)
        self.assertEqual(len(related), 4)
        self.assertNotIn("Montelux", [p["modelo"] for p in related])
        self.assertEqual(len({p["modelo"] for p in related}), 4)

    def test_all_imported_model_pages_render_without_broken_local_media_paths(self):
        for card in reference_cards():
            with self.subTest(model=card["modelo"]):
                response = self.client.get(card["showcase_url"])
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Marca original Poedagar")
                self.assertContains(response, "css/atelier.css")
                self.assertNotContains(response, 'src=""')

    def test_native_admin_and_inventory_require_staff(self):
        for path in ["/admin/", "/admin/catalogo-referencia/", "/admin/catalogo-referencia/inventario.csv"]:
            self.assertEqual(self.client.get(path).status_code, 302)
        user = get_user_model().objects.create_user("ordinary-user", password="isolated-test-only")
        self.client.force_login(user)
        self.assertEqual(self.client.get("/admin/catalogo-referencia/").status_code, 302)

    def test_staff_can_review_sources_errors_and_csv(self):
        user = get_user_model().objects.create_user("catalog-reviewer", password="isolated-test-only", is_staff=True)
        self.client.force_login(user)
        response = self.client.get("/admin/catalogo-referencia/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Montelux")
        self.assertContains(response, "titularidade comercial")
        export = self.client.get("/admin/catalogo-referencia/inventario.csv")
        self.assertEqual(export.status_code, 200)
        self.assertIn("attachment", export["Content-Disposition"])
        self.assertIn("original_url,filename,product,variant,type,resolution", export.content.decode())
        self.assertEqual(self.client.post("/admin/catalogo-referencia/").status_code, 405)
