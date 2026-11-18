from django.test import SimpleTestCase
from urllib.parse import urlencode, parse_qs


class TestSearchSpecialCharacters(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(parse_qs(urlencode({'q': 'A&B'}))['q'], ['A&B'])
