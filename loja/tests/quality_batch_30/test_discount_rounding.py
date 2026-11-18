from django.test import SimpleTestCase
from decimal import Decimal, ROUND_HALF_UP


class TestDiscountRounding(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('10.005').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), Decimal('10.01'))
