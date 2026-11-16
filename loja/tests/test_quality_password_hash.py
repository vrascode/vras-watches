from django.test import SimpleTestCase
from django.contrib.auth.hashers import make_password, check_password


class TestQualityPasswordHash(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(check_password('test-password', make_password('test-password')))
