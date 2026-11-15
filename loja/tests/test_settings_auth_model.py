from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsAuthModel(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.AUTH_USER_MODEL))
