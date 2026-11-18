from django.test import SimpleTestCase
from urllib.parse import urlencode


class TestSearchEncoding(SimpleTestCase):
    def test_behavior(self):
        self.assertIn('q=relogio', urlencode({'q':'relogio'}))
