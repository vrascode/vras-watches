from django.test import SimpleTestCase
from django.contrib.auth.hashers import make_password, check_password


class TestPasswordHash(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(check_password('secret', make_password('secret')))
