"""Public URLs and authenticated sessions survive domain separation."""
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse


class PublicRouteCompatibilityTests(SimpleTestCase):
    def test_existing_names_reverse_and_resolve_without_extra_namespaces(self):
        routes = {
            "home": "/", "products": "/produtos/", "product_detail": "/produto/13/",
            "cart": "/carrinho/", "add_to_cart": "/carrinho/adicionar/13/",
            "remove_from_cart": "/carrinho/remover/13/", "update_cart": "/carrinho/atualizar/13/",
            "catalog_login": "/gestao/entrar/", "catalog_manager": "/gestao/catalogo/",
            "catalog_product": "/gestao/catalogo/13/", "robots": "/robots.txt", "sitemap": "/sitemap.xml",
        }
        for name, path in routes.items():
            with self.subTest(name=name):
                kwargs = {"id": 13} if "13/" in path else {}
                self.assertEqual(reverse(f"loja:{name}", kwargs=kwargs), path)
                self.assertEqual(resolve(path).view_name, f"loja:{name}")


class AuthenticatedSessionCompatibilityTests(TestCase):
    def test_reconciling_legacy_cart_keeps_owner_authenticated(self):
        owner = get_user_model().objects.create_user("compat-owner", is_staff=True)
        self.client.force_login(owner)
        session = self.client.session
        session["cart"] = {"1": 2}
        session["customer_history_reference"] = "existing-history"
        session.save()
        session_key = session.session_key

        self.assertEqual(self.client.get("/carrinho/").status_code, 200)
        self.assertEqual(self.client.session["cart"], {})
        self.assertEqual(self.client.session.session_key, session_key)
        self.assertEqual(self.client.session["customer_history_reference"], "existing-history")
        self.assertEqual(self.client.session["_auth_user_id"], str(owner.pk))
        self.assertEqual(self.client.get("/gestao/catalogo/").status_code, 200)
