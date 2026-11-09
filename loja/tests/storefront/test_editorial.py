from unittest.mock import patch

from django.test import TestCase

from loja.tests.support.catalog import archived_catalog_test


@archived_catalog_test
class StorefrontUpdateTests(TestCase):
    def test_legacy_best_sellers_filter_is_preserved_without_popularity_claim(self):
        response = self.client.get("/produtos/", {"categoria": "Best Sellers"})
        self.assertEqual({p["id"] for p in response.context["products"]}, {4, 8})
        self.assertContains(response, "Seleção VRAS")
        self.assertNotContains(response, ">Best Sellers<")
        self.assertNotContains(response, "Mais vendidos")

    def test_home_style_edits_are_existing_products_and_real_category_links(self):
        response = self.client.get("/")
        groups = response.context["style_edits"]
        self.assertEqual([group["category"] for group in groups], ["Classicos", "Esportivos"])
        self.assertEqual([[p["id"] for p in group["products"]] for group in groups], [[1, 5], [11, 12]])
        self.assertContains(response, "NOSSO ESTILO")
        self.assertNotContains(response, 'href="https://www.instagram.com/p/')

    def test_about_section_remains_when_there_are_no_launches(self):
        with patch("loja.catalog.services.get_new_products", return_value=[]):
            response = self.client.get("/")
        self.assertNotContains(response, 'id="lancamentos"')
        self.assertContains(response, 'id="sobre"')

    def test_mobile_purchase_and_expanded_gallery_keep_existing_cart_route(self):
        response = self.client.get("/produto/2/")
        self.assertContains(response, 'class="detail-purchase"')
        self.assertContains(response, 'action="/carrinho/adicionar/2/"')
        self.assertContains(response, "data-zoom-magnify")
        self.assertContains(response, "data-zoom-prev")
        self.assertContains(response, "data-zoom-next")
        self.assertContains(response, 'href="/produtos/#catalog-search"')
