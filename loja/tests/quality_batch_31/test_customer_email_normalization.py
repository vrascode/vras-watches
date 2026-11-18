from django.test import SimpleTestCase
from django.contrib.auth.models import BaseUserManager


class TestCustomerEmailNormalization(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(BaseUserManager.normalize_email('cliente@EXAMPLE.COM'), 'cliente@example.com')
