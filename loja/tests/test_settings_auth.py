from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsAuth(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.contrib.auth.middleware.AuthenticationMiddleware', settings.MIDDLEWARE)
