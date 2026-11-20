from django.test import SimpleTestCase
from django.conf import settings


class TestRegression08(SimpleTestCase):
    def test_regression(self):
        self.assertIsInstance(settings.ALLOWED_HOSTS, (list, tuple))
