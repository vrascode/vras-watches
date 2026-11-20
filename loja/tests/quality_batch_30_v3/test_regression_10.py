from django.test import SimpleTestCase
from django.conf import settings


class TestRegression10(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(settings.SESSION_COOKIE_NAME)
