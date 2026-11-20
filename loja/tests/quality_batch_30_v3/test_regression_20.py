from django.test import SimpleTestCase
from django.template import engines


class TestRegression20(SimpleTestCase):
    def test_regression(self):
        self.assertGreater(len(engines.all()), 0)
