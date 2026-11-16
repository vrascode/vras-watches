from uuid import uuid4
from django.test import SimpleTestCase


class TestOrderIdentifier(SimpleTestCase):
    def test_generated_identifiers_are_unique(self):
        identifiers = {str(uuid4()) for _ in range(100)}
        self.assertEqual(len(identifiers), 100)
