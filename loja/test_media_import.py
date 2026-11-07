from io import StringIO
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, override_settings
from PIL import Image

from loja import media
from loja.media_import import input_file, prepare_import


class AuthorizedImportTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "midias-instagram"
        self.source.mkdir()
        (self.root / "data").mkdir()
        (self.root / "static").mkdir()
        self.manifest_path = self.root / "data/media.json"
        self.manifest = {"hero": {"image": None}, "products": {}, "instagram": [], "policies": {"QA": "https://example.test"}}
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.catalog_path = self.root / "data/products.json"
        self.catalog = [{"id": 1, "preco": 359}]
        self.catalog_path.write_text(json.dumps(self.catalog), encoding="utf-8")
        Image.new("RGB", (2100, 700), "#334455").save(self.source / "original.jpg", quality=95)
        self.original_bytes = (self.source / "original.jpg").read_bytes()
        self.entry = {"id": "qa-front", "arquivo": "original.jpg", "tipo": "image", "destino": "product",
                      "produto_id": 1, "produto_confirmado": True, "autorizado": True,
                      "origem": "Test-only original", "comprovante": "Test-only permission", "alt": "QA image"}

    def plan(self, entries=None, manifest=None):
        return prepare_import(self.source, {"assets": entries if entries is not None else [self.entry]},
                              self.manifest if manifest is None else manifest, self.catalog)

    def test_responsive_webp_preserves_aspect_and_original(self):
        manifest, files, summary = self.plan()
        asset = manifest["products"]["1"]["images"][0]
        self.assertEqual((asset["width"], asset["height"]), (1920, 640))
        self.assertEqual([item["width"] for item in asset["renditions"]], [480, 800, 1200])
        self.assertEqual(summary["files"], 4)
        self.assertTrue(all(src.endswith(".webp") for src in files))
        self.assertEqual((self.source / "original.jpg").read_bytes(), self.original_bytes)

    def test_unapproved_missing_file_is_skipped(self):
        manifest, files, summary = self.plan([{**self.entry, "autorizado": False, "arquivo": "not-present.jpg"}])
        self.assertEqual(manifest, self.manifest)
        self.assertEqual(files, {})
        self.assertEqual(summary["skipped"], ["qa-front"])

    def test_import_is_idempotent_and_preserves_other_sections(self):
        first, _, _ = self.plan()
        second, _, _ = self.plan(manifest=first)
        self.assertEqual(first, second)
        self.assertEqual(len(second["products"]["1"]["images"]), 1)
        self.assertEqual(second["policies"], self.manifest["policies"])

    def test_mapping_permission_and_permalink_are_required(self):
        for changes in [{"produto_id": 999}, {"produto_confirmado": False}, {"comprovante": ""},
                        {"destino": "instagram", "permalink": "https://www.instagram.com/usevras/"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.plan([{**self.entry, **changes}])

    def test_original_path_cannot_leave_input_folder(self):
        for filename in ["../data/media.json", "https://example.test/image.jpg", "C:\\image.jpg"]:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                input_file(self.source.resolve(), filename)

    def test_video_requires_optimized_confirmation_and_real_poster(self):
        (self.source / "clip.mp4").write_bytes(b"test-only-video-reference")
        entry = {**self.entry, "tipo": "video", "arquivo": "clip.mp4", "poster": "original.jpg"}
        with self.assertRaisesMessage(ValueError, "video_otimizado"):
            self.plan([entry])
        with self.assertRaises(ValueError):
            self.plan([{**entry, "video_otimizado": True, "poster": "missing.jpg"}])

    def test_video_poster_and_captions_are_integrated(self):
        (self.source / "clip.webm").write_bytes(b"test-only-video-reference")
        (self.source / "clip.vtt").write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nQA\n", encoding="utf-8")
        manifest, files, _ = self.plan([{**self.entry, "tipo": "video", "arquivo": "clip.webm",
                                       "poster": "original.jpg", "video_otimizado": True, "legendas": "clip.vtt"}])
        video = manifest["products"]["1"]["videos"][0]
        self.assertIn(video["src"], files)
        self.assertIn(video["poster"]["src"], files)
        self.assertIn(video["captions"]["src"], files)

    def command(self, entries, apply=False):
        (self.source / "manifest.json").write_text(json.dumps({"assets": entries}), encoding="utf-8")
        output = StringIO()
        with (override_settings(BASE_DIR=self.root), patch("loja.media.MEDIA_PATH", self.manifest_path),
              patch("loja.services.PRODUCTS_PATH", self.catalog_path)):
            call_command("import_store_media", source=str(self.source), apply=apply, stdout=output)
        return output.getvalue()

    def test_command_dry_run_does_not_write_store(self):
        output = self.command([self.entry])
        self.assertIn("SIMULAÇÃO", output)
        self.assertEqual(json.loads(self.manifest_path.read_text()), self.manifest)
        self.assertEqual(list((self.root / "static").rglob("*.webp")), [])

    def test_invalid_late_entry_prevents_whole_batch_application(self):
        with self.assertRaises(CommandError):
            self.command([self.entry, {**self.entry, "id": "qa-invalid", "arquivo": "missing.jpg"}], apply=True)
        self.assertEqual(json.loads(self.manifest_path.read_text()), self.manifest)
        self.assertEqual(list((self.root / "static").rglob("*.webp")), [])

    def test_apply_publishes_only_approved_renditions_and_keeps_price(self):
        self.command([self.entry], apply=True)
        with override_settings(BASE_DIR=self.root), patch("loja.media.MEDIA_PATH", self.manifest_path):
            manifest = media.load_media()
            image = media.local_asset(manifest["products"]["1"]["images"][0])
            self.assertEqual(len(image["srcset"].split(",")), 4)
            self.assertEqual(len(media.approved_paths()), 4)
        self.assertEqual(json.loads(self.catalog_path.read_text()), self.catalog)

    def test_instagram_import_requires_real_shaped_link_and_authorized_file(self):
        manifest, _, _ = self.plan([{**self.entry, "destino": "instagram", "permalink": "https://www.instagram.com/p/QA-test-only/"}])
        self.assertEqual(len(manifest["instagram"]), 1)
        for url in ["https://www.instagram.com/p/", "https://user:pass@instagram.com/p/test/", "https://[/p/test/", None]:
            self.assertFalse(media.valid_instagram_permalink(url))

    def test_unapproved_responsive_rendition_is_never_used(self):
        self.command([self.entry], apply=True)
        with override_settings(BASE_DIR=self.root), patch("loja.media.MEDIA_PATH", self.manifest_path):
            entry = media.load_media()["products"]["1"]["images"][0]
            entry["renditions"][0]["autorizado"] = False
            image = media.local_asset(entry)
            self.assertNotIn(" 480w", image["srcset"])
            self.assertEqual(len(image["srcset"].split(",")), 3)
