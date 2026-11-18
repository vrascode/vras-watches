from django.test import SimpleTestCase
from django.core.validators import RegexValidator; from django.core.exceptions import ValidationError


class TestMediaContentType(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(ValidationError, RegexValidator(r'^image/(jpeg|png|webp)$'), 'application/javascript')
