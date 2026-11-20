from django.test import SimpleTestCase
from django.utils.text import get_valid_filename


class TestRegression29(SimpleTestCase):
    def test_regression(self):
        self.assertEqual(get_valid_filename('foto relogio.webp'), 'foto_relogio.webp')
