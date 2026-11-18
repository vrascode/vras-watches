from django.test import SimpleTestCase
from django.core.validators import validate_email; from django.core.exceptions import ValidationError


class TestEmailValidation(SimpleTestCase):
    def test_behavior(self):
        with self.assertRaises(ValidationError):
            validate_email('invalid-email')
