from django.test import SimpleTestCase
from django.contrib.auth import get_backends


class TestQualityAuthBackend(SimpleTestCase):
    def test_behavior(self):
        self.assertGreater(len(get_backends()), 0)
