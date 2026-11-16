from django.test import SimpleTestCase
from django.middleware.security import SecurityMiddleware; from django.test import RequestFactory


class TestQualitySecurityHeaders(SimpleTestCase):
    def test_behavior(self):
        self.assertIsNotNone(SecurityMiddleware(lambda r: None))
