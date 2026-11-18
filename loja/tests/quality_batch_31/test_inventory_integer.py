from django.test import SimpleTestCase
from django.core.validators import validate_integer; from django.core.exceptions import ValidationError


class TestInventoryInteger(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, validate_integer, '2.5')
