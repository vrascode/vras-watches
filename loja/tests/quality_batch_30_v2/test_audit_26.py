from django.test import SimpleTestCase


class TestAudit26(SimpleTestCase):
    def test_project_quality(self):
        from django.utils.text import get_valid_filename
        self.assertNotIn(
            " ",
            get_valid_filename("relogio premium.webp")
        )
