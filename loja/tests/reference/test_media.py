"""The downloader is injected: tests use generated color blocks, never product photos."""
import copy
import hashlib
import tempfile
from io import BytesIO
from pathlib import Path

from django.test import SimpleTestCase
from PIL import Image

from loja.media.reference_inventory import inventory_item, csv_inventory, relative_original_path
from loja.media.reference_pipeline import import_inventory


class ReferenceMediaTests(SimpleTestCase):
    def item(self):
        return inventory_item("https://poedagareco.com/cdn/shop/files/original.png?v=1", "Montelux", "Azul")

    def photo(self):
        output = BytesIO()
        Image.new("RGB", (80, 100), "navy").save(output, "PNG")
        return output.getvalue()

    def test_original_hash_filename_resolution_and_webp(self):
        content = self.photo()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = import_inventory([self.item()], root=root, fetch=lambda url: (content, "image/png"))[0]
            self.assertEqual(item["download_status"], "downloaded")
            self.assertEqual(item["processing_status"], "complete")
            self.assertEqual(item["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual((root / item["original_path"]).read_bytes(), content)
            self.assertTrue(item["original_path"].endswith("/original.png"))
            self.assertIn("/montelux/azul/", item["original_path"])
            self.assertEqual(item["resolution"], {"width": 80, "height": 100})
            for optimized in item["optimized_paths"]:
                with Image.open(root / "static" / optimized) as image:
                    self.assertEqual(image.format, "WEBP")
                    self.assertEqual(image.size, (80, 100))

    def test_reimport_uses_hash_and_never_downloads_again(self):
        with tempfile.TemporaryDirectory() as directory:
            first = import_inventory([self.item()], root=directory, fetch=lambda url: (self.photo(), "image/png"))
            def fail(url):
                raise AssertionError("Original should be reused")
            second = import_inventory(first, root=directory, fetch=fail)
            self.assertEqual(first, second)

    def test_network_failure_does_not_claim_download_or_create_fake_image(self):
        def blocked(url):
            raise OSError("Network blocked")
        with tempfile.TemporaryDirectory() as directory:
            item = import_inventory([self.item()], root=directory, fetch=blocked)[0]
            self.assertEqual(item["download_status"], "error")
            self.assertIn("Network blocked", item["error"])
            self.assertEqual(list(Path(directory).rglob("*")), [])

    def test_invalid_image_preserves_original_but_reports_processing_error(self):
        with tempfile.TemporaryDirectory() as directory:
            item = import_inventory([self.item()], root=directory, fetch=lambda url: (b"invalid", "image/png"))[0]
            self.assertEqual(item["download_status"], "downloaded")
            self.assertEqual(item["processing_status"], "error")
            self.assertEqual((Path(directory) / item["original_path"]).read_bytes(), b"invalid")

    def test_preserved_original_cannot_be_overwritten_by_changed_source(self):
        with tempfile.TemporaryDirectory() as directory:
            first = import_inventory([self.item()], root=directory, fetch=lambda url: (self.photo(), "image/png"))[0]
            item = self.item()
            changed = import_inventory([item], root=directory, fetch=lambda url: (b"changed", "image/png"))[0]
            self.assertEqual(changed["download_status"], "error")
            self.assertEqual((Path(directory) / first["original_path"]).read_bytes(), self.photo())

    def test_rights_status_is_owner_declaration_not_verified_rightsholder(self):
        authorization = self.item()["commercial_authorization"]
        self.assertFalse(authorization["rightsholder_verified"])
        self.assertEqual(authorization["status"], "owner_authorized_unverified_rightsholder")

    def test_shopify_sizes_map_to_the_original_image(self):
        small = inventory_item("https://cdn.shopify.com/watch.png?v=2&width=480", "Montelux")
        large = inventory_item("https://cdn.shopify.com/watch.png?v=2&width=1920", "Montelux")
        self.assertEqual(small["id"], large["id"])
        self.assertEqual(small["original_url"], "https://cdn.shopify.com/watch.png?v=2")
        self.assertIn("width=480", small["observed_urls"][0])

    def test_csv_injection_protection(self):
        item = self.item()
        item["filename"] = "=HYPERLINK(1)"
        self.assertIn("'=HYPERLINK(1)", csv_inventory([item]))

    def test_inventory_identity_cannot_escape_originals_directory(self):
        item = self.item()
        item["id"] = "../../outside"
        with self.assertRaises(ValueError):
            relative_original_path(item)
