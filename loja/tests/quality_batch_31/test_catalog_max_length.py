from django.test import SimpleTestCase
from django.core.validators import MaxLengthValidator; from django.core.exceptions import ValidationError


class TestCatalogMaxLength(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, MaxLengthValidator(120), 'X' * 121)
