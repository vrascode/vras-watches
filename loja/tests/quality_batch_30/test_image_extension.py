from django.test import SimpleTestCase
from pathlib import Path


class TestImageExtension(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Path('watch.WEBP').suffix.lower(), '.webp')
