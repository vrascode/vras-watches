from django.test import SimpleTestCase
from django.core.validators import MinValueValidator; from django.core.exceptions import ValidationError


class TestStockNonnegative(SimpleTestCase):
    def test_behavior(self):
        with self.assertRaises(ValidationError):
            MinValueValidator(0)(-1)
