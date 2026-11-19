from django.test import SimpleTestCase


class TestAudit02(SimpleTestCase):
    def test_project_quality(self):
        from django.urls import get_resolver
        self.assertGreater(len(get_resolver().url_patterns), 0)
