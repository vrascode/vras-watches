from django.test import SimpleTestCase
from uuid import uuid4, UUID


class TestOrderUuid(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(UUID(str(uuid4())).version, 4)
