from django.test import SimpleTestCase


class TestAudit24(SimpleTestCase):
    def test_project_quality(self):
        from django.utils import timezone
        self.assertTrue(
            timezone.is_aware(timezone.now())
        )
