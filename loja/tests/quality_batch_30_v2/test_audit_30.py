from django.test import SimpleTestCase


class TestAudit30(SimpleTestCase):
    def test_project_quality(self):
        from django.core.cache import caches
        cache = caches["default"]
        self.assertNotEqual(
            cache.make_key("product:1"),
            cache.make_key("product:2")
        )
