from django.test import SimpleTestCase
from django.core.validators import MinLengthValidator; from django.core.exceptions import ValidationError


class TestCatalogMinLength(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, MinLengthValidator(3), 'AB')
