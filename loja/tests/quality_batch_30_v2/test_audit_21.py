from django.test import SimpleTestCase


class TestAudit21(SimpleTestCase):
    def test_project_quality(self):
        from django.utils.text import slugify
        self.assertEqual(
            slugify("Relogio Premium"),
            "relogio-premium"
        )
