from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsLanguage(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.LANGUAGE_CODE))
