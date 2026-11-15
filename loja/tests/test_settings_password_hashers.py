from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsPasswordHashers(SimpleTestCase):
    def test_configuration(self):
        self.assertGreater(len(settings.PASSWORD_HASHERS), 0)
