from django.test import SimpleTestCase
from django.http import Http404


class TestQualityHttp404(SimpleTestCase):
    def test_behavior(self):
        self.assertTrue(issubclass(Http404, Exception))
