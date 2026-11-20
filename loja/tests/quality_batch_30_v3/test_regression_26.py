from django.test import SimpleTestCase
from decimal import Decimal


class TestRegression26(SimpleTestCase):
    def test_regression(self):
        self.assertEqual(sum([Decimal('0.10')] * 10), Decimal('1.00'))
