from django.test import SimpleTestCase


class TestAudit18(SimpleTestCase):
    def test_project_quality(self):
        from django.apps import apps
        self.assertTrue(
            all(model._meta.pk is not None for model in apps.get_models())
        )
