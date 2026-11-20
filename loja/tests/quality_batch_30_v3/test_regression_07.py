from django.test import SimpleTestCase
from django.conf import settings


class TestRegression07(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(settings.SECRET_KEY)
