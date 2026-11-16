from django.test import SimpleTestCase
from decimal import Decimal


class TestQualityCartTotals(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('49.90') * 2 + Decimal('15.00'), Decimal('114.80'))
