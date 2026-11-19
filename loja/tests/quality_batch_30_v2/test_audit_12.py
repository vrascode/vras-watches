from django.test import SimpleTestCase


class TestAudit12(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertIn(
            "django.middleware.security.SecurityMiddleware",
            settings.MIDDLEWARE
        )
