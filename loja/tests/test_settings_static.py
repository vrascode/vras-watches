from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsStatic(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.STATIC_URL))
