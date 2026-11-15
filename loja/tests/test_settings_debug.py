from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsDebug(SimpleTestCase):
    def test_configuration(self):
        self.assertIsInstance(settings.DEBUG, bool)
