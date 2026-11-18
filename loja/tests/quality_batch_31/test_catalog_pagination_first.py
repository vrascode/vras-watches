from django.test import SimpleTestCase
from django.core.paginator import Paginator


class TestCatalogPaginationFirst(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(list(Paginator(list(range(12)), 5).page(1)), [0, 1, 2, 3, 4])
