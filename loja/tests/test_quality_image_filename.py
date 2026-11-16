from django.test import SimpleTestCase
from django.utils.text import get_valid_filename


class TestImageFilename(SimpleTestCase):
    def test_filename_sanitization(self):
        filename = get_valid_filename("relogio premium.webp")
        self.assertNotIn(" ", filename)
        self.assertTrue(filename.endswith(".webp"))
