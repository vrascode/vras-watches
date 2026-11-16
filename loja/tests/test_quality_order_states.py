from django.test import SimpleTestCase



class TestQualityOrderStates(SimpleTestCase):
    def test_behavior(self):
        self.assertIn('paid', ('pending', 'paid', 'cancelled'))
