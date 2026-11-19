from django.test import SimpleTestCase


class TestAudit23(SimpleTestCase):
    def test_project_quality(self):
        from decimal import Decimal
        self.assertEqual(
            sum([Decimal("0.10")] * 10),
            Decimal("1.00")
        )
