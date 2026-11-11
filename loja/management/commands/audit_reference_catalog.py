"""Audit the imported subset without changing production offers or fetching files."""
import hashlib
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja.catalog import pricing, repository
from loja.catalog.reference_schema import validate_observation
from loja.media.reference_inventory import relative_original_path


class Command(BaseCommand):
    help = "Confere catálogo de referência, duplicatas, preços e integridade dos originais."

    def add_arguments(self, parser):
        parser.add_argument("--strict-media", action="store_true")

    def handle(self, *args, **options):
        try:
            source = json.loads((settings.BASE_DIR / "data/reference_catalog.json").read_text(encoding="utf-8"))
            for observation in source["products"]:
                validate_observation(observation)
            catalog = repository.load_products()
            imported = [p for p in catalog if p.get("reference_import")]
            ids = [p["id"] for p in catalog]
            keys = [p["reference_key"] for p in imported]
            if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
                raise ValueError("IDs ou variantes duplicados.")
            invalid_prices = [p["id"] for p in imported if not pricing.approved_price(p)]
            if invalid_prices:
                raise ValueError(f"Preços sem aprovação correspondente: {invalid_prices}")
            inventory = json.loads((settings.BASE_DIR / "data/reference_media_inventory.json").read_text(encoding="utf-8"))
            pending, verified = [], []
            for item in inventory["items"]:
                relative = relative_original_path(item)
                if item["download_status"] != "downloaded":
                    pending.append(item["id"])
                    continue
                path = (settings.BASE_DIR / relative).resolve()
                if (not path.is_relative_to((settings.BASE_DIR / "media-originals").resolve())
                        or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]):
                    raise ValueError(f"Original ausente ou hash divergente: {item['id']}")
                verified.append(item["id"])
            report = {"source_models": len(source["products"]), "imported_variants": len(imported),
                      "existing_records": len(catalog) - len(imported), "prices_valid": len(imported),
                      "originals_verified": len(verified), "media_pending": len(pending),
                      "coverage": source.get("coverage"), "complete_media_discovery": False}
            self.stdout.write(json.dumps(report, ensure_ascii=True))
            if options["strict_media"] and pending:
                raise CommandError("Mídias pendentes; auditoria estrita não aprovada.")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
