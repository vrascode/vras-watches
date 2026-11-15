from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsMedia(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(hasattr(settings, 'MEDIA_ROOT'))
