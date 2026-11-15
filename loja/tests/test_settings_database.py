from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsDatabase(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('default', settings.DATABASES)
