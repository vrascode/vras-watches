from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase


class TestCartQuantity(SimpleTestCase):
    def test_zero_quantity_is_rejected(self):
        validator = MinValueValidator(1)
        with self.assertRaises(ValidationError):
            validator(0)
