from django.test import SimpleTestCase
from django.apps import apps


class TestRegression17(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(all(m._meta.db_table for m in apps.get_models()))
