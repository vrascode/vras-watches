from django.test import SimpleTestCase
from django.core.validators import DecimalValidator; from django.core.exceptions import ValidationError; from decimal import Decimal


class TestPriceDecimalPlaces(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, DecimalValidator(8, 2), Decimal('12.345'))
