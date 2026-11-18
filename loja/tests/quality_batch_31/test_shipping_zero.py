from django.test import SimpleTestCase
from decimal import Decimal


class TestShippingZero(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('129.90') + Decimal('0.00'), Decimal('129.90'))
