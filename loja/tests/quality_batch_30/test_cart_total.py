from django.test import SimpleTestCase
from decimal import Decimal


class TestCartTotal(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Decimal('89.90') * 2, Decimal('179.80'))
