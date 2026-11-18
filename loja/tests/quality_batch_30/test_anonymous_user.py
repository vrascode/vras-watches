from django.test import SimpleTestCase
from django.contrib.auth.models import AnonymousUser


class TestAnonymousUser(SimpleTestCase):
    def test_behavior(self):
        self.assertFalse(AnonymousUser().is_authenticated)
