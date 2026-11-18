from django.test import SimpleTestCase
from django.core.paginator import Paginator


class TestPagination(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Paginator(list(range(21)), 10).num_pages, 3)
