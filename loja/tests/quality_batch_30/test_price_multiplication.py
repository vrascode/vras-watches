from django.test import SimpleTestCase
from decimal import Decimal


class TestPriceMultiplication(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('49.90') * 3, Decimal('149.70'))
