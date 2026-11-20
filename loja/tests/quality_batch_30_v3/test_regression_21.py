from django.test import SimpleTestCase
from django.conf import settings


class TestRegression21(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(settings.STATIC_URL)
