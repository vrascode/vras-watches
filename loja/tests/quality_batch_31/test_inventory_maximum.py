from django.test import SimpleTestCase
from django.core.validators import MaxValueValidator; from django.core.exceptions import ValidationError


class TestInventoryMaximum(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, MaxValueValidator(10000), 10001)
