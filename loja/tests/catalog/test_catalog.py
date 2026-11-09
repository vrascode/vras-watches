import io
from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

from loja import utils
from loja.catalog import services
from loja.media import assets as media
from loja.media.staticfiles import ApprovedMediaFinder
from loja.tests.support.catalog import archived_catalog_test


@archived_catalog_test
class CatalogTests(SimpleTestCase):
    def test_all_twelve_products_and_original_media_references_preserved(self):
        catalog = services.get_products()
        self.assertEqual([p["id"] for p in catalog], list(range(1, 13)))
        self.assertEqual(len({p["nome"] for p in catalog}), 12)
        self.assertTrue(all((settings.BASE_DIR / "static/img/products" / p["imagem"]).is_file() for p in catalog))
        self.assertTrue(all(isinstance(p["preco"], Decimal) for p in catalog))

    def test_prices_and_format(self):
        self.assertEqual(services.get_product(1)["preco"], Decimal("359.0"))
        self.assertEqual(utils.format_brl(Decimal("1234.56")), "R$ 1.234,56")

    def test_category_filter_accepts_accents_and_case(self):
        results = services.filter_products(category="CL\u00c1SSICOS")
        self.assertEqual({p["id"] for p in results}, {1, 5, 6})

    def test_query_matches_description_and_name(self):
        self.assertEqual([p["id"] for p in services.filter_products(query="genius")], [2])
        self.assertEqual([p["id"] for p in services.filter_products(query="n\u00e1utica")], [7])

    def test_filters_combine(self):
        self.assertEqual(services.filter_products(category="Maestro", query="Flyback"), [])

    def test_sort_price_both_directions(self):
        for sort, descending in [("preco_asc", False), ("preco_desc", True)]:
            prices = [p["preco"] for p in services.filter_products(sort=sort)]
            self.assertEqual(prices, sorted(prices, reverse=descending))

    def test_sort_names_both_directions(self):
        for sort, descending in [("nome", False), ("nome_desc", True)]:
            names = [utils.normalize(p["nome"]) for p in services.filter_products(sort=sort)]
            self.assertEqual(names, sorted(names, reverse=descending))

    def test_featured_new_and_collections(self):
        self.assertEqual(len(services.get_featured_products()), 5)
        self.assertEqual(len(services.get_collections()), 5)
        self.assertTrue(services.get_product(7)["is_new"])
        self.assertEqual(sum(c["count"] for c in services.get_collections()), 12)

    def test_missing_product(self):
        for value in [999, "invalid", None]:
            self.assertIsNone(services.get_product(value))

    def test_legacy_images_not_implicitly_approved(self):
        self.assertTrue(all(p["cover"] is None for p in services.get_products()))

    def test_catalog_audit(self):
        output = io.StringIO()
        call_command("audit_storefront", stdout=output)
        self.assertIn("12 produtos", output.getvalue())

    def test_unapproved_archive_is_not_published_as_static(self):
        self.assertEqual(media.approved_paths(), set())
        finder = ApprovedMediaFinder()
        self.assertIsNone(finder.find("img/products/41_1200x.webp"))
        self.assertIsNone(finder.find("css/theme.css"))
        self.assertTrue(finder.find("css/premium.css"))

    def test_approved_finder_allowlist(self):
        self.assertTrue(ApprovedMediaFinder.allowed("img/products/real.webp", {"img/products/real.webp"}))
        self.assertFalse(ApprovedMediaFinder.allowed("img/products/other.webp", {"img/products/real.webp"}))
