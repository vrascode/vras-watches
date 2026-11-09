import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


class DeploymentSettingsTests(SimpleTestCase):
    def run_settings(self, **overrides):
        env = os.environ.copy()
        for name in ["DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "SITE_URL", "HTTPS_ENABLED"]:
            env.pop(name, None)
        env.update(DJANGO_DEBUG="false", **overrides)
        return subprocess.run([sys.executable, "-c", "from config import settings; print(settings.CSRF_COOKIE_SECURE, settings.SESSION_COOKIE_SECURE, settings.SECURE_SSL_REDIRECT)"],
                              cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)

    def test_production_refuses_missing_secret(self):
        result = self.run_settings()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_production_refuses_missing_hosts(self):
        result = self.run_settings(DJANGO_SECRET_KEY="test-only-not-a-real-secret")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_enables_https_defaults(self):
        result = self.run_settings(DJANGO_SECRET_KEY="test-only-not-a-real-secret", DJANGO_ALLOWED_HOSTS="example.test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("True True True", result.stdout)

    def test_canonical_origin_rejects_invalid_values(self):
        for url in ["javascript:alert(1)", "https://example.test/path", "https://user:pass@example.test"]:
            result = self.run_settings(DJANGO_SECRET_KEY="test-only-not-a-real-secret", DJANGO_ALLOWED_HOSTS="example.test", SITE_URL=url)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SITE_URL", result.stderr)
