from django.test import SimpleTestCase
from django.core.validators import MaxValueValidator; from django.core.exceptions import ValidationError


class TestUploadLimit(SimpleTestCase):
    def test_behavior(self):
        with self.assertRaises(ValidationError):
            MaxValueValidator(1024)(2048)
