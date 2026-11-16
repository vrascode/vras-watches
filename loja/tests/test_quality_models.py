from django.test import SimpleTestCase
from django.apps import apps


class TestQualityModels(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(apps.ready)
