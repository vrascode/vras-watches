from django.test import SimpleTestCase
from django.utils.http import url_has_allowed_host_and_scheme


class TestSecurityExternalRedirect(SimpleTestCase):
    def test_behavior(self):
        self.assertFalse(url_has_allowed_host_and_scheme('//evil.example/path', allowed_hosts={'example.com'}))
