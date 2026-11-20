from django.test import SimpleTestCase
from django.contrib.auth import get_backends


class TestRegression12(SimpleTestCase):
    def test_regression(self):
        self.assertGreater(len(get_backends()), 0)
