from django.test import SimpleTestCase
from decimal import Decimal


class TestCartTotalPrecision(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(sum([Decimal('0.10')] * 10), Decimal('1.00'))
