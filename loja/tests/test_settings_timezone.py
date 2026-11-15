from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsTimezone(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.TIME_ZONE))
