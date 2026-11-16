from django.test import SimpleTestCase
from pathlib import Path


class TestQualityUploadExtension(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(Path('watch.webp').suffix.lower(), '.webp')
