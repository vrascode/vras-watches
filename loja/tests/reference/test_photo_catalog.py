"""Color isolation, publication boundaries and portable catalogue exports."""
import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.utils.html import escape

from loja.catalog import services
from loja.catalog.preview_photos import photo_index, with_preview_photos


class PhotoCatalogTests(SimpleTestCase):
    def test_every_observed_color_has_its_own_photo_and_remains_unavailable(self):
        from loja.catalog.presentation import showcase_products
        products = showcase_products()
        self.assertEqual(len(products), 48)
        self.assertEqual(len({p["modelo"] for p in products}), 13)
        urls = set()
        for product in products:
            with self.subTest(model=product["modelo"], color=product["reference_color"]):
                self.assertTrue(product["cover"])
                self.assertIn(product["reference_color"], product["cover"]["alt"])
                self.assertFalse(product["can_purchase"])
                urls.add(product["cover"]["url"])
        self.assertEqual(len(urls), 48)
        # Remote previews are absent from the commercial catalogue's local gallery.
        for product in services.get_products(include_drafts=True):
            if product.get("reference_import"):
                self.assertFalse(product["gallery_items"])

    def test_color_navigation_uses_only_selected_variant_photo(self):
        silver = self.client.get("/colecao/montelux/").context["product"]
        response = self.client.get("/colecao/montelux/?cor=Azul")
        blue = response.context["product"]
        self.assertNotEqual(silver["cover"]["url"], blue["cover"]["url"])
        self.assertContains(response, escape(blue["cover"]["url"]), html=False)
        self.assertNotContains(response, "data-add-cart")

    def test_local_gallery_and_published_products_take_precedence(self):
        remote = {("Montelux", "Azul"): [{"url": "https://cdn.shopify.com/blue.png"}]}
        base = {"modelo": "Montelux", "reference_color": "Azul", "reference_import": {},
                "can_purchase": False, "gallery_items": [], "cover": None}
        # A genuine import has non-empty provenance.
        base["reference_import"] = {"source": "observed"}
        local = {**base, "gallery_items": [{"image": {"url": "/static/local.webp"}}],
                 "cover": {"url": "/static/local.webp"}}
        self.assertEqual(with_preview_photos(local, remote), local)
        published = {**base, "can_purchase": True}
        self.assertEqual(with_preview_photos(published, remote), published)
        unknown = {**base, "reference_color": "Unknown"}
        self.assertEqual(with_preview_photos(unknown, remote), unknown)
        self.assertIsNone(base["cover"])

    def test_unassigned_and_untrusted_image_urls_are_excluded(self):
        items = [
            {"product": "Montelux", "variant": "Azul", "type": "image", "role": "product",
             "original_url": "https://untrusted.example/watch.jpg"},
            {"product": "Montelux", "variant": None, "type": "image", "role": "product",
             "original_url": "https://cdn.shopify.com/general.jpg"},
        ]
        with tempfile.TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            path = Path(directory) / "data"
            path.mkdir()
            (path / "reference_media_inventory.json").write_text(json.dumps({"items": items}), encoding="utf-8")
            self.assertEqual(photo_index(), {})
            (path / "reference_media_inventory.json").write_text("invalid", encoding="utf-8")
            self.assertEqual(photo_index(), {})

    def test_print_catalog_has_all_colors_and_filters_one_model(self):
        response = self.client.get("/catalogos/poedagar/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["model_count"], 13)
        self.assertEqual(response.context["color_count"], 48)
        self.assertContains(response, 'class="variant-card"', count=48)
        self.assertContains(response, "Imprimir / Salvar PDF")
        self.assertNotContains(response, "data-add-cart")
        filtered = self.client.get("/catalogos/poedagar/?modelo=Signature")
        self.assertEqual(filtered.context["model_count"], 1)
        self.assertEqual(filtered.context["color_count"], 4)
        self.assertNotContains(filtered, 'id="montelux"')
        self.assertEqual(self.client.get("/catalogos/poedagar/?modelo=Unknown").status_code, 404)
        self.assertEqual(self.client.post("/catalogos/poedagar/").status_code, 405)

    def test_export_generates_fourteen_portable_files_without_mutating_store(self):
        protected = [settings.BASE_DIR / name for name in ("data/products.json", "data/media.json", "db.sqlite3")]
        before = [p.read_bytes() for p in protected]
        with tempfile.TemporaryDirectory() as directory:
            output = StringIO()
            call_command("export_poedagar_catalog", output=directory, stdout=output)
            report = json.loads(output.getvalue())
            self.assertEqual(report["files"], 14)
            self.assertEqual(report["external_images"], 48)
            self.assertEqual(len(list(Path(directory).glob("*.html"))), 14)
            full = (Path(directory) / "index.html").read_text(encoding="utf-8")
            self.assertIn("<style>", full)
            self.assertIn("<script>", full)
            self.assertIn('href="signature.html"', full)
            single = (Path(directory) / "signature.html").read_text(encoding="utf-8")
            self.assertEqual(single.count('class="variant-card"'), 4)
            self.assertIn('href="index.html"', single)
        self.assertEqual([p.read_bytes() for p in protected], before)

    def test_export_can_embed_local_photo_for_offline_use(self):
        from loja.management.commands.export_poedagar_catalog import embed_local_photos
        with tempfile.TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            photo = Path(directory) / "static/test.webp"
            photo.parent.mkdir()
            photo.write_bytes(b"isolated-embedding-fixture")
            context = {"catalog_sections": [{"variants": [{"cover": {"src": "test.webp", "url": "/static/test.webp"}}]}]}
            result = embed_local_photos(context)
            self.assertTrue(result["catalog_sections"][0]["variants"][0]["cover"]["url"].startswith("data:image/webp;base64,"))
            self.assertEqual(context["catalog_sections"][0]["variants"][0]["cover"]["url"], "/static/test.webp")

    @override_settings(SITE_URL="https://vras.example")
    def test_external_open_graph_image_keeps_absolute_source_url(self):
        response = self.client.get("/colecao/montelux/")
        self.assertContains(response, '<meta property="og:image" content="https://poedagareco.com/')
        self.assertNotContains(response, "https://vras.examplehttps://")
