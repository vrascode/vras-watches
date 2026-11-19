from django.test import SimpleTestCase


class TestAudit17(SimpleTestCase):
    def test_project_quality(self):
        from django.apps import apps
        self.assertTrue(
            all(model._meta.app_label for model in apps.get_models())
        )
