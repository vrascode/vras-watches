from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsTemplateBackend(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(any('DjangoTemplates' in t['BACKEND'] for t in settings.TEMPLATES))
