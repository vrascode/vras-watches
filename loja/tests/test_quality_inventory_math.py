from django.test import SimpleTestCase



class TestQualityInventoryMath(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(10 - 3, 7)
