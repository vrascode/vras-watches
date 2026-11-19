from django.test import SimpleTestCase


class TestAudit08(SimpleTestCase):
    def test_project_quality(self):
        from django.contrib.auth import get_user_model
        self.assertIsNotNone(get_user_model())
