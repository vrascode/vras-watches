from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsSecret(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.SECRET_KEY))
