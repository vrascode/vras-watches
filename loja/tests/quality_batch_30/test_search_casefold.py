from django.test import SimpleTestCase



class TestSearchCasefold(SimpleTestCase):
    def test_behavior(self):
        self.assertIn('premium'.casefold(), 'Relogio PREMIUM'.casefold())
