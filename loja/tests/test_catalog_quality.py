from django.test import SimpleTestCase


class CatalogQualityTests(SimpleTestCase):
    def test_product_name_normalization(self):
        name = "  Relogio Poedagar  "
        self.assertEqual(name.strip(), "Relogio Poedagar")

    def test_price_decimal_precision(self):
        from decimal import Decimal

        price = Decimal("199.90")
        self.assertEqual(price * 2, Decimal("399.80"))

    def test_product_reference_normalization(self):
        reference = " pd-001 "
        self.assertEqual(reference.strip().upper(), "PD-001")
