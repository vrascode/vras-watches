from django.test import SimpleTestCase
from django.core.paginator import Paginator


class TestRegression23(SimpleTestCase):
    def test_regression(self):
        self.assertEqual(Paginator(range(31), 10).num_pages, 4)
