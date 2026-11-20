from django.test import SimpleTestCase
from django.conf import settings


class TestRegression09(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(settings.CSRF_COOKIE_NAME)
