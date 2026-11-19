from django.test import SimpleTestCase


class TestAudit03(SimpleTestCase):
    def test_project_quality(self):
        from django.apps import apps
        self.assertGreater(len(list(apps.get_models())), 0)
