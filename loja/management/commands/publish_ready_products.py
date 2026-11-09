"""CLI adapter for the catalog publication service."""
import json

from django.core.management.base import BaseCommand, CommandError

from loja.catalog.publication import publish_ready_products


class Command(BaseCommand):
    help = "Publish only offers passing every existing gate; dry-run by default, prices preserved."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Save only ready draft-to-published transitions")

    def handle(self, *args, **options):
        try:
            result = publish_ready_products(apply=options["apply"])
        except (ValueError, OSError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result, ensure_ascii=True))
