from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsCsrf(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)
