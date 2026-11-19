from django.test import SimpleTestCase


class TestAudit20(SimpleTestCase):
    def test_project_quality(self):
        from django.core.paginator import Paginator
        self.assertEqual(
            Paginator(list(range(21)), 10).num_pages,
            3
        )
