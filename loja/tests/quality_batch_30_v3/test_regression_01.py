from django.test import SimpleTestCase
from django.conf import settings


class TestRegression01(SimpleTestCase):
    def test_regression(self):
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)
