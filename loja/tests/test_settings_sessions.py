from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsSessions(SimpleTestCase):
    def test_configuration(self):
        self.assertIn('django.contrib.sessions', settings.INSTALLED_APPS)
