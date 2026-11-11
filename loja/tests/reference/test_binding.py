"""Media associations cannot silently mix variants or unrelated models."""
import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from PIL import Image

from loja.catalog.reference_import import prepare_catalog
from loja.media.reference_binding import bind_media
from loja.tests.reference.test_import import observation


class ReferenceBindingTests(SimpleTestCase):
    def test_only_exact_known_variant_is_bound_and_reimport_deduplicates(self):
        catalog, _ = prepare_catalog([], [observation()])
        base = {"download_status": "downloaded", "type": "image", "id": "a" * 16,
                "product": "Montelux", "variant": "Azul", "processing_status": "complete",
                "asset": {"src": "test-only.webp", "autorizado": True, "origem": "Temporary QA image only"}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "static").mkdir()
            Image.new("RGB", (8, 10), "navy").save(root / "static/test-only.webp", "WEBP")
            product_path, media_path = root / "data/products.json", root / "data/media.json"
            product_path.write_text(json.dumps(catalog), encoding="utf-8")
            media_path.write_text('{"products":{}}', encoding="utf-8")
            with override_settings(BASE_DIR=root), patch("loja.catalog.repository.PRODUCTS_PATH", product_path), patch("loja.media.assets.MEDIA_PATH", media_path):
                unassigned = {**base, "id": "b" * 16, "variant": None}
                wrong = {**base, "id": "c" * 16, "product": "Different"}
                self.assertEqual(bind_media([base, unassigned, wrong]), ["a" * 16])
                self.assertEqual(bind_media([base]), ["a" * 16])
                snapshot = media_path.read_bytes()
                failed = {**base, "processing_status": "error"}
                absent = {**base, "asset": {**base["asset"], "src": "missing.webp"}}
                self.assertEqual(bind_media([failed, absent]), [])
                self.assertEqual(media_path.read_bytes(), snapshot)
                groups = json.loads(media_path.read_bytes())["products"]
                self.assertEqual(set(groups), {"27"})
                self.assertEqual(len(groups["27"]["images"]), 1)
                self.assertEqual(groups["27"]["images"][0]["source_variant_id"], catalog[2]["variantes_fonte"][0]["source_sku_id"])
