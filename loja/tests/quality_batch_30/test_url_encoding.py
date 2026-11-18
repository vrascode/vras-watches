from django.test import SimpleTestCase
from urllib.parse import quote


class TestUrlEncoding(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(quote('watch premium'), 'watch%20premium')
