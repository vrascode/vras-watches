from django.test import SimpleTestCase
from django.http import JsonResponse


class TestRegression30(SimpleTestCase):
    def test_regression(self):
        self.assertIn('application/json', JsonResponse({'ok': True})['Content-Type'])
