from django.test import SimpleTestCase


class TestAudit10(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertIn(
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            settings.MIDDLEWARE
        )
