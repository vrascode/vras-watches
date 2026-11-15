from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsRootUrlconf(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.ROOT_URLCONF))
