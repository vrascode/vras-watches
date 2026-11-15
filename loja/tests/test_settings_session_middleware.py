from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsSessionMiddleware(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.contrib.sessions.middleware.SessionMiddleware', settings.MIDDLEWARE)
