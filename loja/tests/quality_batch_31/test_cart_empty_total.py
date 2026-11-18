from django.test import SimpleTestCase
from decimal import Decimal


class TestCartEmptyTotal(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(sum([], Decimal('0.00')), Decimal('0.00'))
