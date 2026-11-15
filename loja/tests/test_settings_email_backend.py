from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsEmailBackend(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.EMAIL_BACKEND))
