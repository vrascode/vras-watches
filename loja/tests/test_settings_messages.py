from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsMessages(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.contrib.messages', settings.INSTALLED_APPS)
