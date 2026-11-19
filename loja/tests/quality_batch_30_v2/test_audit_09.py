from django.test import SimpleTestCase


class TestAudit09(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware",
            settings.MIDDLEWARE
        )
