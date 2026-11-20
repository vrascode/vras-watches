from django.test import SimpleTestCase
from django.apps import apps


class TestRegression16(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(all(m._meta.pk is not None for m in apps.get_models()))
