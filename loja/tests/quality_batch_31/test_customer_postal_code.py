from django.test import SimpleTestCase
from django.core.validators import RegexValidator; from django.core.exceptions import ValidationError


class TestCustomerPostalCode(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, RegexValidator(r'^\d{5}-?\d{3}$'), '123')
