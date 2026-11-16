from decimal import Decimal, InvalidOperation
from django.test import SimpleTestCase


class TestPriceValidation(SimpleTestCase):
    def test_invalid_price_is_rejected(self):
        with self.assertRaises(InvalidOperation):
            Decimal("invalid-price")
