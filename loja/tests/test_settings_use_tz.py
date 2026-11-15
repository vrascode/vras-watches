from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsUseTz(SimpleTestCase):
    def test_configuration(self):
        self.assertIsInstance(settings.USE_TZ, bool)
