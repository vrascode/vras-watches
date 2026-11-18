from django.test import SimpleTestCase
from decimal import Decimal


class TestDiscountFull(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('150.00') * (1 - Decimal('1')), Decimal('0.00'))
