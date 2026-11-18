from django.test import SimpleTestCase
from django.core.validators import MinValueValidator


class TestInventoryZero(SimpleTestCase):
    def test_behavior(self):
        self.assertIsNone(MinValueValidator(0)(0))
