import base64
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.contrib.sessions.backends.db import SessionStore
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from loja import media, services
from loja.testing_catalog import archived_catalog_test
from loja.templatetags.store_tags import product_json_ld
from loja.staticfiles import ApprovedMediaFinder


@archived_catalog_test
class CatalogTests(SimpleTestCase):
    def test_all_twelve_products_and_original_media_references_preserved(self):
        catalog = services.get_products()
        self.assertEqual([p["id"] for p in catalog], list(range(1, 13)))
        self.assertEqual(len({p["nome"] for p in catalog}), 12)
        self.assertTrue(all((settings.BASE_DIR / "static/img/products" / p["imagem"]).is_file() for p in catalog))
        self.assertTrue(all(isinstance(p["preco"], Decimal) for p in catalog))

    def test_prices_and_format(self):
        self.assertEqual(services.get_product(1)["preco"], Decimal("359.0"))
        self.assertEqual(services.format_brl(Decimal("1234.56")), "R$ 1.234,56")

    def test_category_filter_accepts_accents_and_case(self):
        results = services.filter_products(category="CL\u00c1SSICOS")
        self.assertEqual({p["id"] for p in results}, {1, 5, 6})

    def test_query_matches_description_and_name(self):
        self.assertEqual([p["id"] for p in services.filter_products(query="genius")], [2])
        self.assertEqual([p["id"] for p in services.filter_products(query="n\u00e1utica")], [7])

    def test_filters_combine(self):
        self.assertEqual(services.filter_products(category="Maestro", query="Flyback"), [])

    def test_sort_price_both_directions(self):
        for sort, descending in [("preco_asc", False), ("preco_desc", True)]:
            prices = [p["preco"] for p in services.filter_products(sort=sort)]
            self.assertEqual(prices, sorted(prices, reverse=descending))

    def test_sort_names_both_directions(self):
        for sort, descending in [("nome", False), ("nome_desc", True)]:
            names = [services.normalize(p["nome"]) for p in services.filter_products(sort=sort)]
            self.assertEqual(names, sorted(names, reverse=descending))

    def test_featured_new_and_collections(self):
        self.assertEqual(len(services.get_featured_products()), 5)
        self.assertEqual(len(services.get_collections()), 5)
        self.assertTrue(services.get_product(7)["is_new"])
        self.assertEqual(sum(c["count"] for c in services.get_collections()), 12)

    def test_missing_product(self):
        for value in [999, "invalid", None]:
            self.assertIsNone(services.get_product(value))

    def test_legacy_images_not_implicitly_approved(self):
        self.assertTrue(all(p["cover"] is None for p in services.get_products()))

    def test_catalog_audit(self):
        output = io.StringIO()
        call_command("audit_storefront", stdout=output)
        self.assertIn("12 produtos", output.getvalue())

    def test_unapproved_archive_is_not_published_as_static(self):
        self.assertEqual(media.approved_paths(), set())
        finder = ApprovedMediaFinder()
        self.assertIsNone(finder.find("img/products/41_1200x.webp"))
        self.assertIsNone(finder.find("css/theme.css"))
        self.assertTrue(finder.find("css/premium.css"))

    def test_approved_finder_allowlist(self):
        self.assertTrue(ApprovedMediaFinder.allowed("img/products/real.webp", {"img/products/real.webp"}))
        self.assertFalse(ApprovedMediaFinder.allowed("img/products/other.webp", {"img/products/real.webp"}))


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
        with patch("loja.media.load_media", return_value=manifest):
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
        with patch("loja.media.load_media", return_value={"products": {"1": {"images": [self.image]}}}):
            response = Client().get("/produto/1/")
            self.assertContains(response, 'type="application/ld+json"')
            self.assertNotContains(response, "aggregateRating")


@archived_catalog_test
class CartTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_add_increments_and_persists_session(self):
        for _ in range(2):
            self.assertEqual(self.client.post("/carrinho/adicionar/1/").status_code, 302)
        self.assertEqual(self.client.session["cart"], {"1": 2})
        response = self.client.get("/carrinho/")
        self.assertEqual(response.context["total"], Decimal("718.00"))
        self.assertContains(response, "R$ 718,00")

    def test_decrement_removes_only_last_unit(self):
        self.client.post("/carrinho/adicionar/1/")
        self.client.post("/carrinho/adicionar/1/")
        self.client.post("/carrinho/remover/1/")
        self.assertEqual(self.client.session["cart"], {"1": 1})
        self.client.post("/carrinho/remover/1/")
        self.assertEqual(self.client.session["cart"], {})

    def test_remove_whole_line(self):
        self.client.post("/carrinho/adicionar/1/")
        self.client.post("/carrinho/adicionar/1/")
        self.client.post("/carrinho/atualizar/1/", {"quantity": "0"})
        self.assertEqual(self.client.session["cart"], {})

    def test_set_quantity_and_total(self):
        self.client.post("/carrinho/atualizar/1/", {"quantity": "3", "preco": "0.01"})
        self.client.post("/carrinho/atualizar/2/", {"quantity": "2"})
        summary = services.cart_summary(self.client.session)
        self.assertEqual(summary["quantity"], 5)
        self.assertEqual(summary["total"], Decimal("1855.00"))

    def test_invalid_quantities_rejected_without_mutation(self):
        self.client.post("/carrinho/adicionar/1/")
        for quantity in ["-1", "100", "1.5", "garbage", "", "1e2"]:
            response = self.client.post("/carrinho/atualizar/1/", {"quantity": quantity})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.client.session["cart"], {"1": 1})

    def test_quantity_cap(self):
        self.client.post("/carrinho/atualizar/1/", {"quantity": "99"})
        self.assertEqual(self.client.post("/carrinho/adicionar/1/").status_code, 400)
        self.assertEqual(self.client.session["cart"]["1"], 99)

    def test_invalid_product_is_404(self):
        for action in ["adicionar", "remover", "atualizar"]:
            self.assertEqual(self.client.post(f"/carrinho/{action}/999/", {"quantity": "1"}).status_code, 404)

    def test_mutations_are_post_only(self):
        for action in ["adicionar", "remover", "atualizar"]:
            self.assertEqual(self.client.get(f"/carrinho/{action}/1/").status_code, 405)

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/carrinho/adicionar/1/").status_code, 403)
        client.get("/produto/1/")
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post("/carrinho/adicionar/1/", {"csrfmiddlewaretoken": token}).status_code, 302)

    def test_redirect_cannot_leave_store(self):
        for destination in ["https://evil.example/", "//evil.example/", "javascript:alert(1)"]:
            response = self.client.post("/carrinho/adicionar/1/", {"next": destination}, HTTP_REFERER=destination)
            self.assertEqual(response["Location"], "/carrinho/")

    def test_internal_redirect_preserves_filters(self):
        response = self.client.post("/carrinho/adicionar/1/", {"next": "/produtos/?q=flyback"})
        self.assertEqual(response["Location"], "/produtos/?q=flyback")

    def test_ajax_json_response_and_count(self):
        response = self.client.post("/carrinho/adicionar/1/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.json()["cart_count"], 1)
        self.assertEqual(response.status_code, 200)

    def test_session_does_not_leak_between_visitors(self):
        self.client.post("/carrinho/adicionar/1/")
        self.assertEqual(services.cart_count(Client().session), 0)

    def test_malformed_and_obsolete_session_entries_ignored(self):
        session = SessionStore()
        session["cart"] = {"1": 2, "2": -3, "3": "5", "999": 1, "4": True, "5": 1000}
        self.assertEqual(services.get_cart(session), {"1": 2, "5": 99})
        session["cart"] = []
        self.assertEqual(services.get_cart(session), {})

    def test_cart_empty_and_no_cache(self):
        response = self.client.get("/carrinho/")
        self.assertContains(response, "carrinho est&aacute; vazio", html=False)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertContains(response, 'content="noindex,follow"')


@archived_catalog_test
class PageTests(TestCase):
    def test_personalized_html_not_cached_by_shared_proxies(self):
        for path in ["/", "/produtos/", "/produto/1/"]:
            self.assertIn("private", self.client.get(path)["Cache-Control"])

    def test_head_supported_for_public_read_routes(self):
        for path in ["/", "/produtos/", "/produto/1/", "/robots.txt", "/sitemap.xml"]:
            self.assertEqual(self.client.head(path).status_code, 200)

    def test_all_routes_and_twelve_detail_pages(self):
        for path in ["/", "/produtos/", "/carrinho/", "/robots.txt", "/sitemap.xml"] + [f"/produto/{id}/" for id in range(1, 13)]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_detail_not_found(self):
        self.assertEqual(self.client.get("/produto/999/").status_code, 404)

    def test_search_sort_and_empty_state(self):
        response = self.client.get("/produtos/", {"categoria": "Maestro", "ordem": "preco_desc"})
        self.assertEqual([p["id"] for p in response.context["products"]], [3, 10, 2])
        self.assertContains(self.client.get("/produtos/?q=does-not-exist"), "Nenhum modelo encontrado")

    def test_bad_sort_falls_back(self):
        self.assertEqual(self.client.get("/produtos/?ordem=bad").context["selected_sort"], "destaques")

    def test_no_unverified_media_false_policies_or_promotions(self):
        response = self.client.get("/")
        for unwanted in ['href="#"', "Google", "Cashback", "5.000 clientes", "DSC00761", "Gemini_Generated", "welcome-modal", 'src="https://']:
            self.assertNotContains(response, unwanted)
        self.assertContains(response, "https://www.instagram.com/usevras/")
        self.assertContains(response, "vrascompany@gmail.com")
        self.assertContains(response, "5563992254787")

    def test_related_products_exclude_current(self):
        response = self.client.get("/produto/1/")
        self.assertEqual(len(response.context["related_products"]), 4)
        self.assertNotIn(1, [p["id"] for p in response.context["related_products"]])

    def test_no_structured_data_without_approved_photo(self):
        self.assertNotContains(self.client.get("/produto/1/"), 'type="application/ld+json"')

    @override_settings(SITE_URL="https://example.test")
    def test_canonical_ignores_query_and_request_host(self):
        response = self.client.get("/produtos/?q=flyback")
        self.assertContains(response, 'rel="canonical" href="https://example.test/produtos/"')

    @override_settings(SITE_URL="https://example.test")
    def test_sitemap_has_exact_public_routes_and_robots_link(self):
        root = ET.fromstring(self.client.get("/sitemap.xml").content)
        locations = [node.text for node in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertEqual(len(locations), 14)
        self.assertNotIn("https://example.test/carrinho/", locations)
        self.assertContains(self.client.get("/robots.txt"), "Sitemap: https://example.test/sitemap.xml")

    @override_settings(SITE_URL="")
    def test_no_invented_production_domain(self):
        self.assertNotContains(self.client.get("/"), 'rel="canonical"')
        self.assertNotContains(self.client.get("/robots.txt"), "Sitemap:")
        self.assertNotContains(self.client.get("/sitemap.xml"), "<loc>")


class DeploymentSettingsTests(SimpleTestCase):
    def run_settings(self, **overrides):
        env = os.environ.copy()
        for name in ["DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "SITE_URL", "HTTPS_ENABLED"]:
            env.pop(name, None)
        env.update(DJANGO_DEBUG="false", **overrides)
        return subprocess.run([sys.executable, "-c", "from config import settings; print(settings.CSRF_COOKIE_SECURE, settings.SESSION_COOKIE_SECURE, settings.SECURE_SSL_REDIRECT)"],
                              cwd=settings.BASE_DIR, env=env, capture_output=True, text=True)

    def test_production_refuses_missing_secret(self):
        result = self.run_settings()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_production_refuses_missing_hosts(self):
        result = self.run_settings(DJANGO_SECRET_KEY="test-only-not-a-real-secret")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_enables_https_defaults(self):
        result = self.run_settings(DJANGO_SECRET_KEY="test-only-not-a-real-secret", DJANGO_ALLOWED_HOSTS="example.test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("True True True", result.stdout)

    def test_canonical_origin_rejects_invalid_values(self):
        for url in ["javascript:alert(1)", "https://example.test/path", "https://user:pass@example.test"]:
            result = self.run_settings(DJANGO_SECRET_KEY="test-only-not-a-real-secret", DJANGO_ALLOWED_HOSTS="example.test", SITE_URL=url)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SITE_URL", result.stderr)
