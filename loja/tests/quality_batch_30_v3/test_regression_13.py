from django.test import SimpleTestCase
from django.conf import settings


class TestRegression13(SimpleTestCase):
    def test_regression(self):
        self.assertIsInstance(settings.AUTH_PASSWORD_VALIDATORS, list)
