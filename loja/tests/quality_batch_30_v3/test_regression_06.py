from django.test import SimpleTestCase
from django.conf import settings


class TestRegression06(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(settings.PASSWORD_HASHERS)
