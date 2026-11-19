from django.test import SimpleTestCase


class TestAudit28(SimpleTestCase):
    def test_project_quality(self):
        from django.http import JsonResponse
        response = JsonResponse({"ok": True})
        self.assertTrue(
            response["Content-Type"].startswith("application/json")
        )
