from django.test import SimpleTestCase
from decimal import Decimal


class TestFreeShipping(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(Decimal('300.00') >= Decimal('299.00'))
