from django.test import SimpleTestCase
from django.utils import timezone


class TestQualityTimezone(SimpleTestCase):
    def test_behavior(self):
        self.assertIsNotNone(timezone.now().tzinfo)
