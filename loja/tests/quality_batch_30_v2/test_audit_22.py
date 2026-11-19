from django.test import SimpleTestCase


class TestAudit22(SimpleTestCase):
    def test_project_quality(self):
        from decimal import Decimal
        self.assertEqual(
            Decimal("19.90") * 3,
            Decimal("59.70")
        )
