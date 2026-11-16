from django.test import SimpleTestCase
from uuid import uuid4


class TestQualityUuid(SimpleTestCase):
    def test_behavior(self):
        self.assertNotEqual(uuid4(), uuid4())
