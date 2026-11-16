from django.test import SimpleTestCase
from django.template import engines


class TestQualityTemplates(SimpleTestCase):
    def test_behavior(self):
        self.assertGreater(len(engines.all()), 0)
