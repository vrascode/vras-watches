from django.test import SimpleTestCase
from django.core.validators import MaxLengthValidator; from django.core.exceptions import ValidationError


class TestCatalogSlugLength(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, MaxLengthValidator(80), 'a' * 81)
