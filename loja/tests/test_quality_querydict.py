from django.test import SimpleTestCase
from django.http import QueryDict


class TestQualityQuerydict(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(QueryDict('item=1&item=2').getlist('item'), ['1', '2'])
