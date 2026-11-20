from django.test import SimpleTestCase
from django.urls import get_resolver


class TestRegression19(SimpleTestCase):
    def test_regression(self):
        self.assertGreater(len(get_resolver().url_patterns), 0)
