from django.test import SimpleTestCase


class TestAudit16(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertTrue(bool(settings.DATABASES["default"]["ENGINE"]))
