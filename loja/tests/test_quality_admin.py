from django.test import SimpleTestCase
from django.contrib import admin


class TestQualityAdmin(SimpleTestCase):
    def test_behavior(self):
        self.assertIsNotNone(admin.site)
