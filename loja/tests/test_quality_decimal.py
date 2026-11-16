from django.test import SimpleTestCase
from decimal import Decimal


class TestQualityDecimal(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('19.90') + Decimal('10.10'), Decimal('30.00'))
