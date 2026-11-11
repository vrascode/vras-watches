"""Public source adapters never import promotional HTML as storefront copy."""
import json
from unittest.mock import patch

from django.test import SimpleTestCase

from loja.catalog.shopify_source import normalize_product, ProductHTML, discover_urls, fetch_product
from loja.media.public_download import validate_public_url
from loja.media.reference_inventory import discover_inventory


def shopify_product():
    return {"id": 7, "title": "Relógio Poedagar Montelux®",
            "description": '<ul><li>Movimento: Quartzo</li><li>Peso: 88 g</li></ul><p>EXCLUSIVE AD COPY</p>',
            "variants": [{"id": 91, "title": "Prata", "price": 25900, "available": True, "featured_image": {"id": 8}}],
            "media": [{"id": 8, "media_type": "image", "src": "https://cdn.shopify.com/watch.png", "width": 1000, "height": 1200}]}


URL = "https://poedagareco.com/products/relogio-poedagar-montelux"


class SourceTests(SimpleTestCase):
    def test_cents_variant_id_and_specs_preserved_without_ad_copy(self):
        source = normalize_product(shopify_product(), URL)
        self.assertEqual(source["price_brl"], "259.00")
        self.assertEqual(source["variants"][0]["source_id"], 91)
        self.assertEqual(source["specifications"], {"Movimento": "Quartzo", "Peso": "88 g"})
        self.assertNotIn("EXCLUSIVE AD COPY", source["description"])
        self.assertEqual(source["brand"], "Poedagar")

    def test_invalid_response_and_non_watch_are_rejected(self):
        for raw in ({}, {"variants": [{}], "title": "Óculos Poedagar"}, {**shopify_product(), "variants": [{"id": 1, "title": "X", "price": 259.0}]}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_product(raw, URL)

    def test_variant_featured_image_is_mapped_exactly(self):
        source = normalize_product(shopify_product(), URL)
        inventory = discover_inventory(source)
        self.assertEqual(inventory[0]["variant"], "Prata")
        self.assertEqual(inventory[0]["resolution"], {"width": 1000, "height": 1200})

    def test_all_video_encodings_and_editorial_media_are_inventoried(self):
        source = normalize_product(shopify_product(), URL)
        source["media"].append({"media_type": "video", "sources": [
            {"format": "mp4", "url": "https://cdn.shopify.com/video-720.mp4", "width": 720, "height": 900},
            {"format": "mp4", "url": "https://cdn.shopify.com/video-1080.mp4", "width": 1080, "height": 1350}]})
        source["description_media"] = ["https://poedagareco.com/cdn/shop/files/detail.png"]
        source["page_media"] = ["https://cdn.shopify.com/theme-video.mp4"]
        inventory = discover_inventory(source)
        self.assertEqual(len(inventory), 5)
        self.assertEqual(sum(i["type"] == "video" for i in inventory), 3)
        self.assertTrue(all(i["variant"] is None for i in inventory if i["type"] == "video"))

    def test_media_parser_extracts_lazy_sources_and_srcset(self):
        parser = ProductHTML()
        parser.feed('<video poster="//cdn.shopify.com/poster.png"><source data-src="//cdn.shopify.com/clip.mp4"></video><img srcset="//cdn.shopify.com/a.png 480w, //cdn.shopify.com/b.png 800w">')
        self.assertEqual(len(parser.media), 4)

    def test_ssrf_auth_and_unapproved_hosts_rejected(self):
        for url in ["http://poedagareco.com/a.png", "https://127.0.0.1/a.png",
                    "https://user:pass@poedagareco.com/a.png", "https://poedagareco.com.evil.example/a.png",
                    "https://cdn.shopify.com:8443/a.png"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_public_url(url, resolve=False)
        with patch("loja.media.public_download.socket.getaddrinfo", return_value=[(None, None, None, None, ("127.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                validate_public_url("https://poedagareco.com/a.png")

    def test_full_page_discovers_theme_video_and_skips_unapproved_hosts(self):
        markup = '<video><source src="https://cdn.shopify.com/theme.mp4"></video><img src="/cdn/shop/files/detail.png"><img src="https://unapproved.example/other.png">'
        with patch("loja.catalog.shopify_source.download", side_effect=[
                (json.dumps(shopify_product()).encode(), "application/json"), (markup.encode(), "text/html")]):
            source, _ = fetch_product(URL)
        self.assertIn("https://cdn.shopify.com/theme.mp4", source["page_media"])
        self.assertIn("https://poedagareco.com/cdn/shop/files/detail.png", source["page_media"])
        self.assertFalse(any("unapproved" in url for url in source["page_media"]))

    def test_catalog_discovery_reaches_terminal_page(self):
        with patch("loja.catalog.shopify_source.download", return_value=('{"products":[{"title":"Relogio X","handle":"x"},{"title":"Relógio Poedagar Montelux","handle":"montelux"}]}'.encode("utf-8"), "application/json")):
            self.assertEqual(discover_urls(), ["https://poedagareco.com/products/montelux"])
