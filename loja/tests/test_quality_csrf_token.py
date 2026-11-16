from django.test import SimpleTestCase
from django.middleware.csrf import get_token; from django.test import RequestFactory


class TestQualityCsrfToken(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(bool(get_token(RequestFactory().get('/'))))
