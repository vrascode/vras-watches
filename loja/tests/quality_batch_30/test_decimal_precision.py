from django.test import SimpleTestCase
from decimal import Decimal


class TestDecimalPrecision(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('0.1') + Decimal('0.2'), Decimal('0.3'))
