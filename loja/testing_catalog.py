"""Archived catalog fixtures for pre-migration component regression tests only.

Publication rules are tested independently in test_catalog_migration.py. These
fixtures never alter the production JSON, session database or media manifest.
"""
import functools
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


ARCHIVE = Path(__file__).resolve().parent.parent / "data/backups/catalog-before-poedagar-91f8988/products.json"


def legacy_catalog():
    rows = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    for row in rows:
        row["status"] = "publicado"
        row["catalog_generation"] = "legacy"
    return rows


def archived_catalog_test(cls):
    original_setup = cls.setUp

    @functools.wraps(original_setup)
    def setup(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "products.json"
        path.write_text(json.dumps(legacy_catalog()), encoding="utf-8")
        for mocked in [patch("loja.services.PRODUCTS_PATH", path),
                       patch("loja.services.publication_issues", return_value=[])]:
            mocked.start()
            self.addCleanup(mocked.stop)
        original_setup(self)

    cls.setUp = setup
    return cls
