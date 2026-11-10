from pathlib import Path
from django.test import SimpleTestCase


class ProjectIntegrityTest(SimpleTestCase):
    def test_source_file_exists(self):
        root = Path(__file__).resolve().parents[3]
        target = root / "loja/tests/catalog/test_publication.py"
        self.assertTrue(target.is_file())

    def test_source_file_is_not_empty(self):
        root = Path(__file__).resolve().parents[3]
        target = root / "loja/tests/catalog/test_publication.py"
        self.assertGreater(target.stat().st_size, 0)
