from django.test import SimpleTestCase
from django.core.validators import MinValueValidator; from django.core.exceptions import ValidationError


class TestCartQuantity(SimpleTestCase):
    def test_behavior(self):
        with self.assertRaises(ValidationError):
            MinValueValidator(1)(0)
