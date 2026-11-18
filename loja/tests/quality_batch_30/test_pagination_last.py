from django.test import SimpleTestCase
from django.core.paginator import Paginator


class TestPaginationLast(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(len(Paginator(list(range(21)), 10).page(3)), 1)
