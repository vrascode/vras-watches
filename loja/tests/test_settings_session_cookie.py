from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsSessionCookie(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.SESSION_COOKIE_NAME))
