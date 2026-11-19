from django.test import SimpleTestCase


class TestAudit07(SimpleTestCase):
    def test_project_quality(self):
        from django.contrib.auth import get_backends
        self.assertGreater(len(get_backends()), 0)
