from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsDatabaseEngine(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.DATABASES['default']['ENGINE']))
