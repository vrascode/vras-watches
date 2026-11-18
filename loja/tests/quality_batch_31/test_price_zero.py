from django.test import SimpleTestCase
from decimal import Decimal


class TestPriceZero(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('0.00'), Decimal(0))
