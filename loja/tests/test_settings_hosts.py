from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsHosts(SimpleTestCase):
    def test_configuration(self):
        self.assertIsInstance(settings.ALLOWED_HOSTS, (list, tuple))
