from django.test import SimpleTestCase


class TestAudit25(SimpleTestCase):
    def test_project_quality(self):
        from uuid import uuid4, UUID
        identifier = str(uuid4())
        self.assertEqual(
            str(UUID(identifier)),
            identifier
        )
