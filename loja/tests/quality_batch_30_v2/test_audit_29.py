from django.test import SimpleTestCase


class TestAudit29(SimpleTestCase):
    def test_project_quality(self):
        from django.utils.http import url_has_allowed_host_and_scheme
        self.assertFalse(
            url_has_allowed_host_and_scheme(
                "https://evil.example/",
                allowed_hosts={"example.com"}
            )
        )
