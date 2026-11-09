import base64
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import Client, override_settings, SimpleTestCase

from loja.catalog import services
from loja.media import assets as media
from loja.templatetags.store_tags import product_json_ld
from loja.tests.support.catalog import archived_catalog_test


@archived_catalog_test
class MediaTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        static = self.root / "static/img/products"
        static.mkdir(parents=True)
        # Test-only image fixture; never copied into the public catalog.
        (static / "test.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII="))
        (static / "test.mp4").write_bytes(b"test-only-reference")
        self.override = override_settings(BASE_DIR=self.root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.image = {"src": "img/products/test.png", "origem": "test fixture", "autorizado": True}
        self.video = {"src": "img/products/test.mp4", "origem": "test fixture", "autorizado": True,
                      "poster": self.image}

    def test_approved_local_image(self):
        self.assertEqual(media.local_asset(self.image)["url"], "/static/img/products/test.png")

    def test_unapproved_or_missing_provenance_rejected(self):
        for entry in [None, {}, {**self.image, "autorizado": False}, {**self.image, "origem": ""}]:
            self.assertIsNone(media.local_asset(entry))

    def test_missing_remote_and_traversal_paths_rejected(self):
        for src in ["../secret.png", "/etc/test.png", "img/products/missing.png", "https://cdn.example/test.png", "C:\\test.png"]:
            self.assertIsNone(media.local_asset({**self.image, "src": src}))

    def test_video_requires_approved_poster(self):
        self.assertEqual(media.local_asset(self.video, "video")["mime"], "video/mp4")
        self.assertIsNone(media.local_asset({**self.video, "poster": None}, "video"))

    def test_video_extension_required(self):
        self.assertIsNone(media.local_asset(self.image, "video"))

    def test_instagram_requires_real_post_path_and_local_media(self):
        entry = {"permalink": "https://www.instagram.com/reel/test-fixture/", "image": self.image}
        self.assertEqual(len(media.instagram_posts({"instagram": [entry]})), 1)
        for url in ["https://www.instagram.com/usevras/", "https://evil.example/reel/test/", "javascript:alert(1)"]:
            self.assertEqual(media.instagram_posts({"instagram": [{**entry, "permalink": url}]}), [])

    def test_optional_product_gallery_supports_multiple_videos(self):
        manifest = {"products": {"1": {"images": [self.image], "videos": [self.video, self.video]}}}
        with patch("loja.media.assets.load_media", return_value=manifest):
            product = services.get_product(1)
            self.assertEqual(len(product["images"]), 1)
            self.assertEqual(len(product["videos"]), 2)

    def test_structured_data_escapes_script_injection(self):
        payload = str(product_json_ld({"name": "</script><script>alert(1)</script>"}))
        self.assertEqual(payload.count("</script>"), 1)
        self.assertIn('type="application/ld+json"', payload)
        self.assertIn("\\u003C", payload)

    @override_settings(SITE_URL="https://example.test")
    def test_product_schema_only_when_media_is_approved(self):
        with patch("loja.media.assets.load_media", return_value={"products": {"1": {"images": [self.image]}}}):
            response = Client().get("/produto/1/")
            self.assertContains(response, 'type="application/ld+json"')
            self.assertNotContains(response, "aggregateRating")
