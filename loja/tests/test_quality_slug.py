from django.test import SimpleTestCase
from django.utils.text import slugify


class TestQualitySlug(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(slugify('Relogio Premium'), 'relogio-premium')
