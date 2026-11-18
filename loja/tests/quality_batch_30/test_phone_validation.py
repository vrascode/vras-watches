from django.test import SimpleTestCase
from django.core.validators import RegexValidator; from django.core.exceptions import ValidationError


class TestPhoneValidation(SimpleTestCase):
    def test_behavior(self):
        with self.assertRaises(ValidationError):
            RegexValidator(r'^\d{11}$')('invalid')
