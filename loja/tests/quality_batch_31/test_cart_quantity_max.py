from django.test import SimpleTestCase
from django.core.validators import MaxValueValidator; from django.core.exceptions import ValidationError


class TestCartQuantityMax(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, MaxValueValidator(99), 100)
