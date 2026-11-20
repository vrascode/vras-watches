from django.test import SimpleTestCase
from django.conf import settings


class TestRegression15(SimpleTestCase):
    def test_regression(self):
        self.assertTrue(settings.DATABASES['default']['ENGINE'])
