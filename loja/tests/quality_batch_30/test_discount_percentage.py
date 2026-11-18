from django.test import SimpleTestCase
from decimal import Decimal


class TestDiscountPercentage(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('200') * Decimal('0.10'), Decimal('20.00'))
