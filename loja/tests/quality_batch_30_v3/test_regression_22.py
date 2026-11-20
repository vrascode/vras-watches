from django.test import SimpleTestCase
from django.conf import settings


class TestRegression22(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(hasattr(settings, 'MEDIA_ROOT'))
