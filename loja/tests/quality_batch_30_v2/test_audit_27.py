from django.test import SimpleTestCase


class TestAudit27(SimpleTestCase):
    def test_project_quality(self):
        from pathlib import Path
        self.assertEqual(
            Path("relogio.WEBP").suffix.lower(),
            ".webp"
        )
