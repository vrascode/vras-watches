from django.test import SimpleTestCase
from django.core.cache import caches


class TestCacheKeys(SimpleTestCase):
    def test_behavior(self):
        self.assertNotEqual(caches['default'].make_key('product:1'), caches['default'].make_key('product:2'))
