from django.test import SimpleTestCase
from urllib.parse import urlencode


class TestQualityUrlEncoding(SimpleTestCase):
    def test_behavior(self):
        self.assertIn('q=relogio', urlencode({'q': 'relogio'}))
