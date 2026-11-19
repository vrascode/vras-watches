from django.test import SimpleTestCase


class TestAudit01(SimpleTestCase):
    def test_project_quality(self):
        from django.apps import apps
        self.assertTrue(apps.ready)
