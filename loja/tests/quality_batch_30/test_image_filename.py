from django.test import SimpleTestCase
from django.utils.text import get_valid_filename


class TestImageFilename(SimpleTestCase):
    def test_behavior(self):
        self.assertNotIn(' ', get_valid_filename('watch premium.webp'))
