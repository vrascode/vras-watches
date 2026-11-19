from django.test import SimpleTestCase


class TestAudit04(SimpleTestCase):
    def test_project_quality(self):
        from django.template import engines
        self.assertGreater(len(engines.all()), 0)
