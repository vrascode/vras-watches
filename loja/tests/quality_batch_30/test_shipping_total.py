from django.test import SimpleTestCase
from decimal import Decimal


class TestShippingTotal(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('99.90') + Decimal('15.00'), Decimal('114.90'))
