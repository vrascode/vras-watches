"""Retry media without changing catalogue/prices/database or confusing transport and HTTP."""
import json
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings
from PIL import Image

from loja.catalog.reference_import import prepare_catalog
from loja.media.download_diagnostics import describe_failure
from loja.media.reference_inventory import inventory_item
from loja.media.reference_pipeline import import_inventory
from loja.tests.reference.test_import import observation


class DownloadFailureTests(SimpleTestCase):
    def test_local_socket_denial_is_not_reported_as_origin_http_block(self):
        failure = describe_failure(URLError(PermissionError(13, "Socket denied by environment")))
        self.assertEqual(failure["code"], "environment_network_denied")
        self.assertIsNone(failure["http_status"])
        self.assertFalse(failure["retryable_without_access_change"])

    def test_http_access_and_rate_limits_are_reported_separately(self):
        for status, code in [(401, "source_authentication_required"), (403, "source_access_denied"),
                             (404, "source_not_found"), (429, "source_rate_limited")]:
            with self.subTest(status=status):
                result = describe_failure(HTTPError("https://cdn.shopify.com/test.png", status, "HTTP failure", {}, None))
                self.assertEqual(result["code"], code)
                self.assertEqual(result["http_status"], status)
                self.assertEqual(result["retryable_without_access_change"], status == 429)

    def test_processing_failure_does_not_claim_download_failure(self):
        self.assertEqual(describe_failure(ValueError("Invalid photo"), "processing")["code"], "media_processing_failed")


class MediaOnlyRetryTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "data").mkdir()
        products, _ = prepare_catalog([], [observation()])
        self.path = self.root / "data/products.json"
        self.path.write_text(json.dumps(products), encoding="utf-8")
        self.database = self.root / "db.sqlite3"
        self.database.write_bytes(b"database must remain byte-identical")
        self.manifest = self.root / "data/media.json"
        self.manifest.write_text('{"products":{}}', encoding="utf-8")
        self.inventory_path = self.root / "data/reference_media_inventory.json"
        self.item = inventory_item("https://cdn.shopify.com/QA-only.png", "Montelux", "Azul")
        self.inventory_path.write_text(json.dumps({"schema_version": 1, "discovery_status": "preserve scope", "items": [self.item]}), encoding="utf-8")
        self.before_catalog, self.before_database = self.path.read_bytes(), self.database.read_bytes()
        for context in (override_settings(BASE_DIR=self.root),
                        patch("loja.catalog.repository.PRODUCTS_PATH", self.path),
                        patch("loja.media.assets.MEDIA_PATH", self.manifest)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def run_retry(self, fetch, **options):
        output = StringIO()
        with patch("loja.management.commands.retry_reference_media.import_inventory",
                   side_effect=lambda items: import_inventory(items, fetch=fetch)):
            call_command("retry_reference_media", stdout=output, **options)
        return json.loads(output.getvalue())

    def assert_preserved(self):
        self.assertEqual(self.path.read_bytes(), self.before_catalog)
        self.assertEqual(self.database.read_bytes(), self.before_database)
        self.assertEqual(json.loads(self.inventory_path.read_bytes())["discovery_status"], "preserve scope")

    def test_dry_run_does_not_download_or_modify_inventory(self):
        before = self.inventory_path.read_bytes()
        def should_not_fetch(url):
            raise AssertionError("Dry run must not perform network I/O")
        result = self.run_retry(should_not_fetch)
        self.assertFalse(result["applied"])
        self.assertEqual(self.inventory_path.read_bytes(), before)
        self.assert_preserved()

    def test_success_attaches_exact_variant_without_claiming_offer_publication(self):
        output = BytesIO()
        Image.new("RGB", (16, 20), "navy").save(output, "PNG")
        result = self.run_retry(lambda url: (output.getvalue(), "image/png"), apply=True, publish_ready=True)
        self.assertEqual(result["images_verified"], 1)
        self.assertEqual(result["videos_verified"], 0)
        self.assertEqual(result["media_attached"], 1)
        self.assertEqual(result["published_products"], [])
        self.assertEqual(result["purchasable_products"], 0)
        self.assertEqual(set(json.loads(self.manifest.read_bytes())["products"]), {"27"})
        self.assert_preserved()

    def test_blocked_retry_saves_precise_diagnostics_without_fake_gallery_or_publication(self):
        def blocked(url):
            raise URLError(PermissionError(13, "Local socket permission denied"))
        with self.assertRaises(CommandError):
            self.run_retry(blocked, apply=True, publish_ready=True)
        item = json.loads(self.inventory_path.read_bytes())["items"][0]
        self.assertEqual(item["failure"]["code"], "environment_network_denied")
        self.assertIsNone(item["failure"]["http_status"])
        self.assertEqual(item["download_status"], "error")
        self.assertFalse(item.get("asset"))
        self.assertEqual(self.manifest.read_text(encoding="utf-8"), '{"products":{}}')
        self.assert_preserved()

    def test_publish_option_requires_apply(self):
        with self.assertRaisesMessage(CommandError, "exige --apply"):
            self.run_retry(lambda url: None, publish_ready=True)
