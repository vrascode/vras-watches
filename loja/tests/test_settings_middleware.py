from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsMiddleware(SimpleTestCase):
    def test_configuration(self):
        self.assertGreater(len(settings.MIDDLEWARE), 0)
