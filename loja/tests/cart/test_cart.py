from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import Client, TestCase

from loja.cart import services as cart_services
from loja.tests.support.catalog import archived_catalog_test


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
        summary = cart_services.cart_summary(self.client.session)
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
        self.assertEqual(cart_services.cart_count(Client().session), 0)

    def test_malformed_and_obsolete_session_entries_ignored(self):
        session = SessionStore()
        session["cart"] = {"1": 2, "2": -3, "3": "5", "999": 1, "4": True, "5": 1000}
        self.assertEqual(cart_services.get_cart(session), {"1": 2, "5": 99})
        session["cart"] = []
        self.assertEqual(cart_services.get_cart(session), {})

    def test_cart_empty_and_no_cache(self):
        response = self.client.get("/carrinho/")
        self.assertContains(response, "carrinho est&aacute; vazio", html=False)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertContains(response, 'content="noindex,follow"')
