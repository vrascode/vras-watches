from django.test import SimpleTestCase
from django.conf import settings


class TestRegression05(SimpleTestCase):
    def test_regression(self):
        self.assertIn('django.middleware.clickjacking.XFrameOptionsMiddleware', settings.MIDDLEWARE)
