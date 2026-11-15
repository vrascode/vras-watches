from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsTemplates(SimpleTestCase):
    def test_configuration(self):
        self.assertGreater(len(settings.TEMPLATES), 0)
