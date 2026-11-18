from django.test import SimpleTestCase
from decimal import Decimal


class TestPriceStringConversion(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(str(Decimal('149.90')), '149.90')
