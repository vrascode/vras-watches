from django.test import SimpleTestCase
from django.contrib.staticfiles import finders


class TestQualityStaticfiles(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(callable(finders.find))
