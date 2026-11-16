from django.test import SimpleTestCase
from django.urls import get_resolver


class TestQualityUrlconf(SimpleTestCase):
    def test_behavior(self):
        self.assertGreater(len(get_resolver().url_patterns), 0)
