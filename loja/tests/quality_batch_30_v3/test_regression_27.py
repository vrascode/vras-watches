from django.test import SimpleTestCase
from uuid import UUID, uuid4


class TestRegression27(SimpleTestCase):
    def test_regression(self):
        self.assertEqual(UUID(str(uuid4())).version, 4)
