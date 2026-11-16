from django.test import SimpleTestCase
from django.utils.html import escape


class TestQualityHtmlEscape(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(escape('<script>'), '&lt;script&gt;')
