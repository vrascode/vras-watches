from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsSecurityMiddleware(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.middleware.security.SecurityMiddleware', settings.MIDDLEWARE)
