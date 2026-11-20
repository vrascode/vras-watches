from django.test import SimpleTestCase
from django.conf import settings


class TestRegression14(SimpleTestCase):
    def test_regression(self):
        self.assertIn('default', settings.DATABASES)
