from django.test import SimpleTestCase
from decimal import Decimal, ROUND_DOWN


class TestPriceRoundDown(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('10.999').quantize(Decimal('0.01'), rounding=ROUND_DOWN), Decimal('10.99'))
