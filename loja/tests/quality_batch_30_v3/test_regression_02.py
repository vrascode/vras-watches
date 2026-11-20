from django.test import SimpleTestCase
from django.conf import settings


class TestRegression02(SimpleTestCase):
    def test_regression(self):
        self.assertIn('django.middleware.security.SecurityMiddleware', settings.MIDDLEWARE)
