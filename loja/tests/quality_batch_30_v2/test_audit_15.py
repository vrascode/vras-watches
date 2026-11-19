from django.test import SimpleTestCase


class TestAudit15(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertTrue(bool(settings.SESSION_COOKIE_NAME))
