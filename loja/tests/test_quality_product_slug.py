from django.test import SimpleTestCase
from django.utils.text import slugify


class TestProductSlug(SimpleTestCase):
    def test_slug_normalization(self):
        self.assertEqual(
            slugify("Relogio Masculino Premium"),
            "relogio-masculino-premium"
        )
