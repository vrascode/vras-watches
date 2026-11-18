from django.test import SimpleTestCase
from django.utils import timezone


class TestOrderTimestamp(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(timezone.is_aware(timezone.now()))
