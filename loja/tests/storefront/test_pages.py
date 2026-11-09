import xml.etree.ElementTree as ET

from django.test import override_settings, TestCase

from loja.tests.support.catalog import archived_catalog_test


@archived_catalog_test
class PageTests(TestCase):
    def test_personalized_html_not_cached_by_shared_proxies(self):
        for path in ["/", "/produtos/", "/produto/1/"]:
            self.assertIn("private", self.client.get(path)["Cache-Control"])

    def test_head_supported_for_public_read_routes(self):
        for path in ["/", "/produtos/", "/produto/1/", "/robots.txt", "/sitemap.xml"]:
            self.assertEqual(self.client.head(path).status_code, 200)

    def test_all_routes_and_twelve_detail_pages(self):
        for path in ["/", "/produtos/", "/carrinho/", "/robots.txt", "/sitemap.xml"] + [f"/produto/{id}/" for id in range(1, 13)]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_detail_not_found(self):
        self.assertEqual(self.client.get("/produto/999/").status_code, 404)

    def test_search_sort_and_empty_state(self):
        response = self.client.get("/produtos/", {"categoria": "Maestro", "ordem": "preco_desc"})
        self.assertEqual([p["id"] for p in response.context["products"]], [3, 10, 2])
        self.assertContains(self.client.get("/produtos/?q=does-not-exist"), "Nenhum modelo encontrado")

    def test_bad_sort_falls_back(self):
        self.assertEqual(self.client.get("/produtos/?ordem=bad").context["selected_sort"], "destaques")

    def test_no_unverified_media_false_policies_or_promotions(self):
        response = self.client.get("/")
        for unwanted in ['href="#"', "Google", "Cashback", "5.000 clientes", "DSC00761", "Gemini_Generated", "welcome-modal", 'src="https://']:
            self.assertNotContains(response, unwanted)
        self.assertContains(response, "https://www.instagram.com/usevras/")
        self.assertContains(response, "vrascompany@gmail.com")
        self.assertContains(response, "5563992254787")

    def test_related_products_exclude_current(self):
        response = self.client.get("/produto/1/")
        self.assertEqual(len(response.context["related_products"]), 4)
        self.assertNotIn(1, [p["id"] for p in response.context["related_products"]])

    def test_no_structured_data_without_approved_photo(self):
        self.assertNotContains(self.client.get("/produto/1/"), 'type="application/ld+json"')

    @override_settings(SITE_URL="https://example.test")
    def test_canonical_ignores_query_and_request_host(self):
        response = self.client.get("/produtos/?q=flyback")
        self.assertContains(response, 'rel="canonical" href="https://example.test/produtos/"')

    @override_settings(SITE_URL="https://example.test")
    def test_sitemap_has_exact_public_routes_and_robots_link(self):
        root = ET.fromstring(self.client.get("/sitemap.xml").content)
        locations = [node.text for node in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertEqual(len(locations), 14)
        self.assertNotIn("https://example.test/carrinho/", locations)
        self.assertContains(self.client.get("/robots.txt"), "Sitemap: https://example.test/sitemap.xml")

    @override_settings(SITE_URL="")
    def test_no_invented_production_domain(self):
        self.assertNotContains(self.client.get("/"), 'rel="canonical"')
        self.assertNotContains(self.client.get("/robots.txt"), "Sitemap:")
        self.assertNotContains(self.client.get("/sitemap.xml"), "<loc>")
