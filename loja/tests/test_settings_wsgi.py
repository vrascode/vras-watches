from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsWsgi(SimpleTestCase):
    def test_configuration(self):
        self.assertTrue(bool(settings.WSGI_APPLICATION))
