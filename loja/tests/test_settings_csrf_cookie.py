from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsCsrfCookie(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.CSRF_COOKIE_NAME))
