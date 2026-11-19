from django.test import SimpleTestCase


class TestAudit06(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertTrue(hasattr(settings, "MEDIA_ROOT"))
