from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsLoginUrl(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.LOGIN_URL))
