"""Production migration checks; publication gates are never mocked here."""
import base64
import copy
import json
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.core.management import call_command, CommandError
from django.test import override_settings, TestCase

from loja.cart import services as cart_services
from loja.catalog import pricing, services


class CatalogMigrationTests(TestCase):
    def test_twelve_distinct_real_commercial_models_replace_legacy_ids(self):
        catalog = [p for p in services.get_products(include_drafts=True) if not p.get("reference_import")]
        self.assertEqual([p["id"] for p in catalog], list(range(13, 25)))
        self.assertEqual(len({p["slug"] for p in catalog}), 12)
        self.assertEqual({p["modelo"] for p in catalog}, {
            "Army", "Deluxe", "Deluxe Golden", "Golden Mars", "Golden Moon", "Golden Neptune",
            "Golden Star", "King Royal", "Machine", "Nautilus", "Signature", "Tempus"})
        self.assertTrue(all(p["fontes"]["nome_comercial_verificado"] for p in catalog))
        self.assertTrue(all(p["fontes"]["url_modelo_e_preco"].startswith("https://lojaspoedagar.com.br/") for p in catalog))

    def test_priced_models_remain_draft_without_identity_media_and_offer(self):
        self.assertEqual(services.get_products(), [])
        for product in services.get_products(include_drafts=True):
            with self.subTest(product=product["id"]):
                self.assertEqual(product["status"], "rascunho")
                self.assertGreater(product["preco"], 0)
                self.assertIsNone(product["cover"])
                self.assertIsNone(product["imagem"])
                self.assertFalse(product["can_purchase"])
                self.assertTrue(product["aprovacao_preco"]["aprovado"])
                self.assertTrue(pricing.approved_price(product))
                self.assertNotIn("preco_sem_aprovacao_correspondente", product["publication_issues"])
                self.assertNotIn("??", product["descricao"])

    def test_archive_is_versioned_and_matches_recorded_hashes(self):
        import hashlib
        folder = settings.BASE_DIR / "data/backups/catalog-before-poedagar-91f8988"
        recorded = json.loads((folder / "backup.json").read_text(encoding="utf-8"))
        for name, digest in recorded["files"].items():
            self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
        old = json.loads((folder / "products.json").read_text(encoding="utf-8"))
        self.assertEqual([p["id"] for p in old], list(range(1, 13)))

    def test_drafts_do_not_leak_via_home_search_or_direct_urls(self):
        for route in ["/", "/produtos/", "/produtos/?q=Army", "/produtos/?categoria=Poedagar"]:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "data-add-cart")
            self.assertNotContains(response, "Vras Flyback")
            self.assertNotContains(response, "196,92")
            self.assertNotContains(response, 'class="product-card"')
        for product_id in range(13, 25):
            self.assertEqual(self.client.get(f"/produto/{product_id}/").status_code, 404)

    def test_old_bookmarks_redirect_to_catalog_without_reassigning_identity(self):
        for product_id in range(1, 13):
            response = self.client.get(f"/produto/{product_id}/")
            self.assertRedirects(response, "/produtos/", fetch_redirect_response=False)

    def test_old_cart_is_cleared_with_notice_and_other_session_data_preserved(self):
        session = self.client.session
        session["cart"] = {"1": 2, "12": 1}
        session["customer_history_reference"] = "preserve-this-value"
        session.save()
        response = self.client.get("/carrinho/")
        self.assertContains(response, "Itens antigos ou indisponíveis foram removidos")
        self.assertEqual(self.client.session["cart"], {})
        self.assertEqual(self.client.session["customer_history_reference"], "preserve-this-value")
        self.assertEqual(response.context["total"], Decimal("0.00"))
        self.assertNotContains(self.client.get("/carrinho/"), "Itens antigos ou indisponíveis foram removidos")

    def test_current_generation_draft_cart_is_also_reconciled(self):
        session = SessionStore()
        session["cart"] = {"13": 2}
        session[cart_services.CART_VERSION_KEY] = "poedagar-v1"
        self.assertEqual(cart_services.get_cart(session), {})
        self.assertEqual(session["cart"], {})

    def test_post_cannot_buy_retired_or_draft_models(self):
        for product_id in list(range(1, 13)) + list(range(13, 25)):
            for action in ["adicionar", "atualizar"]:
                response = self.client.post(f"/carrinho/{action}/{product_id}/", {"quantity": 1, "preco": "0.01"})
                self.assertEqual(response.status_code, 404)
        self.assertEqual(cart_services.cart_count(self.client.session), 0)

    @override_settings(SITE_URL="https://example.test")
    def test_sitemap_has_no_draft_or_retired_product(self):
        response = self.client.get("/sitemap.xml")
        self.assertNotContains(response, "/produto/")


class PublicationAndCartTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "products.json"
        self.product = copy.deepcopy(services.get_products(include_drafts=True)[0])
        self.product.update(nome="Produto fictício QA", marca="Marca QA", modelo="Modelo QA", referencia="QA-ONLY", preco=199.90,
                            status="publicado", oferta_confirmada=True)
        self.product["identificacao"] = {"confirmada": True, "marca": "Marca QA", "modelo": "Modelo QA",
                                           "referencia": "QA-ONLY", "fonte": "https://supplier.example.test/manual"}
        self.product["variante"] = {"confirmada": True, "cor": "Azul QA", "pulseira": "Pulseira QA",
                                    "fonte": "https://supplier.example.test/manual", "source_variant_id": 123}
        self.product["variantes_fonte"] = [{"source_sku_id": 123}]
        self.product["aprovacao_preco"] = {"aprovado": True, "valor": "199.90", "data": "2026-11-07", "registro": "Test-only approval", "source_variant_id": 123}
        self.asset_dir = tempfile.TemporaryDirectory(prefix="qa-migration-", dir=settings.BASE_DIR / "static/img/products")
        self.addCleanup(self.asset_dir.cleanup)
        image = Path(self.asset_dir.name) / "fixture.png"
        image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII="))
        self.asset = {"src": image.relative_to(settings.BASE_DIR / "static").as_posix(), "autorizado": True,
                      "origem": "Temporary fixture only", "produto_id": 13, "catalog_generation": "poedagar-v1",
                      "modelo": "Modelo QA", "source_variant_id": 123}
        for mock in [patch("loja.catalog.repository.PRODUCTS_PATH", self.path),
                     patch("loja.media.assets.load_media", return_value={"products": {"13": {"images": [self.asset]}}})]:
            mock.start()
            self.addCleanup(mock.stop)
        self.save()

    def save(self):
        self.path.write_text(json.dumps([self.product]), encoding="utf-8")

    def test_complete_approved_fixture_is_visible_and_cart_uses_approved_price(self):
        self.assertEqual([p["id"] for p in services.get_products()], [13])
        response = self.client.get("/produto/13/")
        self.assertContains(response, "R$ 199,90")
        self.client.post("/carrinho/atualizar/13/", {"quantity": 2, "preco": "0.01"})
        self.assertEqual(cart_services.cart_summary(self.client.session)["total"], Decimal("399.80"))
        self.assertEqual(self.client.session[cart_services.CART_VERSION_KEY], "poedagar-v1")

    def test_published_flag_alone_cannot_bypass_missing_approval_identity_variant_or_offer(self):
        for field, value in [("aprovacao_preco", {}), ("identificacao", {}), ("variante", None),
                             ("oferta_confirmada", False), ("status", "rascunho")]:
            with self.subTest(field=field):
                old = copy.deepcopy(self.product[field])
                self.product[field] = value
                self.save()
                self.assertEqual(services.get_products(), [])
                self.assertEqual(self.client.post("/carrinho/adicionar/13/").status_code, 404)
                self.product[field] = old

    def test_stale_price_approval_cannot_authorize_different_price(self):
        self.product["preco"] = 249.90
        self.save()
        self.assertEqual(services.get_products(), [])
        with self.assertRaisesMessage(CommandError, "publicação bloqueada"):
            call_command("audit_storefront")

    def test_photo_for_another_sku_or_generation_cannot_publish(self):
        for field, value in [("produto_id", 1), ("catalog_generation", "legacy"), ("autorizado", False),
                             ("modelo", "Outro modelo"), ("source_variant_id", 456)]:
            old = self.asset[field]
            self.asset[field] = value
            self.assertEqual(services.get_products(), [])
            self.asset[field] = old

    def test_withdrawn_approval_removes_existing_cart_item(self):
        self.client.post("/carrinho/adicionar/13/")
        self.product["aprovacao_preco"]["aprovado"] = False
        self.save()
        response = self.client.get("/carrinho/")
        self.assertEqual(response.context["quantity"], 0)
        self.assertContains(response, "Itens antigos ou indisponíveis foram removidos")

    def test_variant_must_match_the_recorded_source(self):
        self.product["variante"]["source_variant_id"] = 999
        self.save()
        self.assertEqual(services.get_products(), [])

    def test_price_approval_cannot_be_reused_for_another_variant(self):
        self.product["aprovacao_preco"]["source_variant_id"] = 456
        self.save()
        self.assertEqual(services.get_products(), [])

    def test_retired_id_cannot_be_reused_even_with_approved_fixture(self):
        self.product["id"] = 1
        self.save()
        self.assertEqual(services.get_products(), [])

    def test_correct_cover_does_not_allow_wrong_variant_in_secondary_gallery(self):
        wrong = {**self.asset, "source_variant_id": 456}
        with patch("loja.media.assets.load_media", return_value={"products": {"13": {"images": [self.asset, wrong]}}}):
            self.assertEqual(services.get_products(), [])

    def test_identity_reference_and_model_must_match_the_product(self):
        for field in ("marca", "modelo", "referencia"):
            old = self.product["identificacao"][field]
            self.product["identificacao"][field] = "Other QA"
            self.save()
            self.assertEqual(services.get_products(), [])
            self.product["identificacao"][field] = old
