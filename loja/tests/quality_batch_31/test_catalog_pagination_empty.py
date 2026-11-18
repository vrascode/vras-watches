from django.test import SimpleTestCase
from django.core.paginator import Paginator


class TestCatalogPaginationEmpty(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Paginator([], 10).num_pages, 1)
