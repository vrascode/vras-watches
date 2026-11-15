from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsUseI18n(SimpleTestCase):
    def test_configuration(self):
        self.assertIsInstance(settings.USE_I18N, bool)
