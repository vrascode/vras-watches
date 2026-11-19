from django.test import SimpleTestCase


class TestAudit05(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertTrue(bool(settings.STATIC_URL))
