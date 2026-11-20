from django.test import SimpleTestCase
from django.apps import apps


class TestRegression18(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(apps.ready)
