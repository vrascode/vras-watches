from django.test import SimpleTestCase
from django.http import JsonResponse


class TestJsonResponse(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(JsonResponse({'ok':True}).status_code, 200)
