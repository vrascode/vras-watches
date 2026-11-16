from django.test import SimpleTestCase
from django.http import HttpResponseRedirect


class TestQualityRedirect(SimpleTestCase):
    def test_behavior(self):
        self.assertEqual(HttpResponseRedirect('/').status_code, 302)
