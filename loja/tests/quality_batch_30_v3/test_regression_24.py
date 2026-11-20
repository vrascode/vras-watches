from django.test import SimpleTestCase
from django.utils.text import slugify


class TestRegression24(SimpleTestCase):
    def test_regression(self):
        self.assertEqual(slugify('Relogio Premium'), 'relogio-premium')
