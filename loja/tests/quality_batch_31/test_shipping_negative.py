from django.test import SimpleTestCase
from django.core.validators import MinValueValidator; from django.core.exceptions import ValidationError


class TestShippingNegative(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, MinValueValidator(0), -10)
