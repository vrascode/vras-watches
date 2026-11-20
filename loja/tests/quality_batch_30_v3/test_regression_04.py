from django.test import SimpleTestCase
from django.conf import settings


class TestRegression04(SimpleTestCase):
    def test_regression(self):
        self.assertIn('django.contrib.sessions.middleware.SessionMiddleware', settings.MIDDLEWARE)
