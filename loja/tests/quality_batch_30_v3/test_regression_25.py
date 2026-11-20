from django.test import SimpleTestCase
from decimal import Decimal


class TestRegression25(SimpleTestCase):
    def test_regression(self):
        self.assertEqual(Decimal('29.90') * 3, Decimal('89.70'))
