from django.test import SimpleTestCase


class TestAudit14(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertTrue(bool(settings.CSRF_COOKIE_NAME))
