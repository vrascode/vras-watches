from django.test import SimpleTestCase
from django.contrib.auth import get_user_model


class TestRegression11(SimpleTestCase):
    def test_regression(self):
        self.assertIsNotNone(get_user_model())
