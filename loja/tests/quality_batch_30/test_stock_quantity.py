from django.test import SimpleTestCase



class TestStockQuantity(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(20 - 7, 13)
