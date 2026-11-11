"""Offline tests use synthetic images only inside temporary fixture directories."""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings
from PIL import Image

from loja.catalog import services
from loja.catalog.reference_import import prepare_catalog
from loja.media.local_reference import (authorized_image, download_plan, finalize_download,
                                        inspect_image, inspect_original, media_status, original_path)
from loja.media.reference_inventory import inventory_item
from loja.tests.reference.test_import import observation


SOURCE_ROOT = settings.BASE_DIR


class LocalReferenceTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "data").mkdir()
        self.catalog_path = self.root / "data/products.json"
        products, _ = prepare_catalog([], [observation()])
        self.catalog_path.write_text(json.dumps(products), encoding="utf-8")
        self.database = self.root / "db.sqlite3"
        self.database.write_bytes(b"unchanged database fixture")
        self.manifest = self.root / "data/media.json"
        self.manifest.write_text('{"products":{}}', encoding="utf-8")
        self.inventory_path = self.root / "data/reference_media_inventory.json"
        self.item = inventory_item("https://cdn.shopify.com/local-only-blue.png", "Montelux", "Azul")
        self.save_inventory([self.item])
        self.protected_before = (self.catalog_path.read_bytes(), self.database.read_bytes())
        for context in (override_settings(BASE_DIR=self.root),
                        patch("loja.catalog.repository.PRODUCTS_PATH", self.catalog_path),
                        patch("loja.media.assets.MEDIA_PATH", self.manifest)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def save_inventory(self, items):
        self.inventory_path.write_text(json.dumps({"schema_version": 1, "scope": "preserve fixture", "items": items}), encoding="utf-8")

    def create_original(self, item=None, color="navy"):
        item = item or self.item
        staging = self.root / "media-originals/.incoming"
        staging.mkdir(parents=True, exist_ok=True)
        candidate = staging / (item["id"] + ".part")
        Image.new("RGB", (640, 800), color).save(candidate, "PNG")
        receipt = finalize_download(self.root, item, candidate)
        candidate.unlink()
        return receipt

    def run_import(self, **options):
        output = StringIO()
        with patch("socket.socket.connect", side_effect=AssertionError("Offline import must never open a socket")):
            call_command("import_poedagar_media", stdout=output, **options)
        return json.loads(output.getvalue())

    def assert_protected(self):
        self.assertEqual((self.catalog_path.read_bytes(), self.database.read_bytes()), self.protected_before)

    def test_authorization_requires_record_and_rejects_revocation(self):
        self.assertTrue(authorized_image(self.item))
        for authorization in ({}, {"confirmed": True}, {"record": "fixture", "status": "pending"},
                              {**self.item["commercial_authorization"], "revoked": True},
                              {**self.item["commercial_authorization"], "confirmed": False},
                              {"record": "fixture", "confirmed": True, "status": "revoked"}):
            self.assertFalse(authorized_image({**self.item, "commercial_authorization": authorization}))

    def test_valid_original_is_preserved_and_second_plan_reuses_it(self):
        receipt = self.create_original()
        path = original_path(self.root, self.item)
        before = path.read_bytes()
        self.assertEqual(receipt["transport"], "PowerShell Invoke-WebRequest")
        self.assertEqual(receipt["sha256"], inspect_original(self.root, self.item)["sha256"])
        self.assertEqual(download_plan(self.root)["items"][0]["action"], "reuse")
        self.assertEqual(media_status(self.root)["downloads_completed"], 1)
        self.assertEqual(path.read_bytes(), before)

    def test_corrupt_existing_original_is_not_replaced(self):
        self.create_original()
        target = original_path(self.root, self.item)
        target.write_bytes(b"corrupt original must remain untouched")
        self.assertEqual(download_plan(self.root)["items"][0]["action"], "error")
        with self.assertRaises((OSError, ValueError)):
            inspect_original(self.root, self.item)
        self.assertEqual(target.read_bytes(), b"corrupt original must remain untouched")

    def test_changed_valid_original_is_rejected_by_hash(self):
        self.create_original()
        target = original_path(self.root, self.item)
        Image.new("RGB", (640, 800), "red").save(target, "PNG")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            inspect_original(self.root, self.item)
        self.assertEqual(download_plan(self.root)["items"][0]["action"], "error")

    def test_invalid_formats_dimensions_and_file_sizes(self):
        path = self.root / "bad.part"
        path.write_bytes(b"<html>not a photograph</html>")
        with self.assertRaises(OSError):
            inspect_image(path)
        Image.new("RGB", (12, 12)).save(path, "GIF")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            inspect_image(path)
        Image.new("RGB", (12, 12)).save(path, "PNG")
        with patch("loja.media.local_reference.MAX_PIXELS", 100):
            with self.assertRaisesRegex(ValueError, "megapixels"):
                inspect_image(path)
        with patch("loja.media.local_reference.MAX_BYTES", 8):
            with self.assertRaisesRegex(ValueError, "bytes"):
                inspect_image(path)
        path.write_bytes(path.read_bytes()[:40])
        with self.assertRaises((OSError, ValueError, SyntaxError)):
            inspect_image(path)

    def test_path_escape_url_and_identity_are_rejected(self):
        for field, value in [("filename", "../escape.png"), ("filename", "CON.jpg"),
                             ("id", "b" * 16), ("original_url", "http://cdn.shopify.com/watch.png")]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    original_path(self.root, {**self.item, field: value})
        outside = self.root / "outside.png"
        Image.new("RGB", (10, 10)).save(outside)
        with self.assertRaisesRegex(ValueError, "staging"):
            finalize_download(self.root, self.item, outside)

    def test_identical_inventory_duplicates_are_downloaded_once_and_conflicts_fail(self):
        self.save_inventory([self.item, copy.deepcopy(self.item)])
        self.assertEqual(len(download_plan(self.root)["items"]), 1)
        self.save_inventory([self.item, {**self.item, "variant": "Preto"}])
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            download_plan(self.root)

    def test_apply_generates_webp_thumbnail_exact_color_and_repeat_has_no_duplicates(self):
        receipt = self.create_original()
        first = self.run_import(apply=True)
        self.assertEqual(first["valid_images"], 1)
        self.assertEqual(first["products_with_gallery"], 1)
        self.assertEqual(first["media_pending"], 0)
        self.assertEqual(first["published_products"], [])
        self.assertEqual(set(json.loads(self.manifest.read_bytes())["products"]), {"27"})
        product = next(p for p in services.get_products(include_drafts=True) if p["id"] == 27)
        self.assertEqual(product["images"][0]["width"], 640)
        self.assertIn("160w", product["images"][0]["srcset"])
        self.assertFalse(product["can_purchase"])
        item = json.loads(self.inventory_path.read_bytes())["items"][0]
        self.assertTrue(any(path.endswith("-160.webp") for path in item["optimized_paths"]))
        before = self.manifest.read_bytes()
        self.run_import(apply=True)
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertEqual(inspect_original(self.root, self.item)["sha256"], receipt["sha256"])
        self.assert_protected()

    def test_unassigned_photo_is_processed_but_never_assigned_by_guess(self):
        self.item["variant"] = None
        self.save_inventory([self.item])
        self.create_original()
        report = self.run_import(apply=True)
        self.assertEqual(report["valid_images"], 1)
        self.assertEqual(report["imported_images"], 1)
        self.assertEqual(report["products_with_gallery"], 0)
        self.assertEqual(report["media_pending"], 1)
        self.assert_protected()

    def test_unauthorized_image_is_skipped_without_modifying_gallery(self):
        self.item["commercial_authorization"] = {}
        self.save_inventory([self.item])
        self.assertEqual(download_plan(self.root)["items"][0]["action"], "skip")
        report = self.run_import(apply=True)
        self.assertEqual(report["images_authorized"], 0)
        self.assertEqual(report["eligible_local_images"], 0)
        self.assertEqual(json.loads(self.manifest.read_bytes()), {"products": {}})

    def test_dry_run_does_not_process_or_mutate_catalog_inventory_or_receipts(self):
        self.create_original()
        inventory_before = self.inventory_path.read_bytes()
        report = self.run_import()
        self.assertEqual(report["eligible_local_images"], 1)
        self.assertEqual(report["imported_images"], 0)
        self.assertEqual(self.inventory_path.read_bytes(), inventory_before)
        self.assertFalse((self.root / "static").exists())
        self.assert_protected()

    def test_missing_file_failure_is_reported_and_valid_files_still_import(self):
        missing = inventory_item("https://cdn.shopify.com/missing.png", "Montelux", "Prata")
        self.save_inventory([self.item, missing])
        self.create_original()
        with self.assertRaises(CommandError):
            self.run_import(apply=True)
        report = json.loads((self.root / "artifacts/catalogos/poedagar/local-import-report.json").read_bytes())
        self.assertEqual(report["imported_images"], 1)
        self.assertEqual(report["download_pending"], 1)
        self.assertIn(missing["id"], report["missing_or_invalid_originals"])
        self.assert_protected()

    def test_cli_planning_works_without_django_database_or_network(self):
        completed = subprocess.run([sys.executable, str(SOURCE_ROOT / "scripts/poedagar_media.py"),
                                    "--root", str(self.root), "plan"],
                                   capture_output=True, text=True, timeout=15, check=True)
        self.assertEqual(json.loads(completed.stdout)["items"][0]["action"], "download")
        self.assertFalse((self.root / "media-originals").exists())

    def test_powershell_script_parses_without_executing_or_changing_policy(self):
        executable = shutil.which("powershell") or shutil.which("pwsh")
        if not executable:
            self.skipTest("PowerShell is unavailable")
        path = str(SOURCE_ROOT / "scripts/download_poedagar_media.ps1").replace("'", "''")
        command = "$e=$null; $t=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('" + path + "',[ref]$t,[ref]$e); if($e.Count){$e; exit 1}"
        result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", command],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
