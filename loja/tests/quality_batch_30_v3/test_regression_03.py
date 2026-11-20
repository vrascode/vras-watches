from django.test import SimpleTestCase
from django.conf import settings


class TestRegression03(SimpleTestCase):
    def test_regression(self):
        self.assertIn('django.contrib.auth.middleware.AuthenticationMiddleware', settings.MIDDLEWARE)
