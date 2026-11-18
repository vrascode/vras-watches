from django.test import SimpleTestCase
from django.core.files.utils import validate_file_name; from django.core.exceptions import SuspiciousFileOperation


class TestMediaFilenameSafety(SimpleTestCase):
    def test_behavior(self):
        self.assertRaises(SuspiciousFileOperation, validate_file_name, '../secret.txt')
