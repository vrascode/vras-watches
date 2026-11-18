from django.test import SimpleTestCase
from django.utils.html import escape


class TestHtmlEscape(SimpleTestCase):
    def test_behavior(self):
        self.assertIn('&lt;', escape('<script>'))
