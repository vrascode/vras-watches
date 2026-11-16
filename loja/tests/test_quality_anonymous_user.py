from django.test import SimpleTestCase
from django.contrib.auth.models import AnonymousUser


class TestQualityAnonymousUser(SimpleTestCase):
    def test_behavior(self):
        self.assertFalse(AnonymousUser().is_authenticated)
