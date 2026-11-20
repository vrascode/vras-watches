from django.test import SimpleTestCase
from django.utils import timezone


class TestRegression28(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(timezone.is_aware(timezone.now()))
