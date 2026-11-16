from django.test import SimpleTestCase


class TestProductSearch(SimpleTestCase):
    def test_case_insensitive_matching(self):
        product = "Relogio Masculino Premium"
        search = "PREMIUM"
        self.assertIn(search.casefold(), product.casefold())
