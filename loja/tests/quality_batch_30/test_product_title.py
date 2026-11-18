from django.test import SimpleTestCase
from django.core.validators import MaxLengthValidator; from django.core.exceptions import ValidationError


class TestProductTitle(SimpleTestCase):
    def test_behavior(self):
        with self.assertRaises(ValidationError):
            MaxLengthValidator(100)('A' * 101)
