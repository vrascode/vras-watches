from django.test import SimpleTestCase


class TestAudit19(SimpleTestCase):
    def test_project_quality(self):
        from django.apps import apps
        self.assertTrue(
            all(model._meta.db_table for model in apps.get_models())
        )
