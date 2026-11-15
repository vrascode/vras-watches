from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsInstalledApps(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.contrib.auth', settings.INSTALLED_APPS)
