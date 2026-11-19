from django.test import SimpleTestCase


class TestAudit13(SimpleTestCase):
    def test_project_quality(self):
        from django.conf import settings
        self.assertGreater(len(settings.PASSWORD_HASHERS), 0)
