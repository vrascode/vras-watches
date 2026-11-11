"""Retry public media only: never reimport products, reapprove prices or mutate SQLite."""
import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja.catalog import services
from loja.catalog.publication import publish_ready_products
from loja.catalog.reference_storage import atomic_write, catalog_lock, encode
from loja.media import assets as media
from loja.media.reference_binding import bind_media
from loja.media.reference_inventory import csv_inventory
from loja.media.reference_pipeline import import_inventory


class Command(BaseCommand):
    help = "Tenta novamente mídias públicas preservando produtos, preços e banco; simula por padrão."

    def add_arguments(self, parser):
        parser.add_argument("--model")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--publish-ready", action="store_true")
        parser.add_argument("--report")

    def handle(self, *args, **options):
        try:
            if options["publish_ready"] and not options["apply"]:
                raise ValueError("--publish-ready exige --apply.")
            path = settings.BASE_DIR / "data/reference_media_inventory.json"
            original = path.read_bytes()
            inventory = json.loads(original)
            selected = [item for item in inventory["items"] if not options["model"]
                        or item["product"].casefold() == options["model"].casefold()]
            if not selected:
                raise ValueError("Nenhuma mídia correspondente no inventário.")
            report = {"applied": options["apply"], "selected": len(selected),
                      "images_verified": 0, "videos_verified": 0, "media_attached": 0,
                      "published_products": [], "failures": {}}
            if options["apply"]:
                processed = import_inventory(selected)
                indexed = {item["id"]: item for item in processed}
                updated = {**inventory, "items": [indexed.get(item["id"], item) for item in inventory["items"]]}
                with catalog_lock():
                    atomic_write(path, encode(updated), expected=original)
                    atomic_write(settings.BASE_DIR / "data/reference_media_inventory.csv",
                                 csv_inventory(updated["items"]).encode("utf-8-sig"))
                report["media_attached"] = len(bind_media(processed))
                for item in processed:
                    kind = item["type"]
                    if (item.get("download_status") == "downloaded" and item.get("processing_status") == "complete"
                            and media.local_asset(item.get("asset"), kind)):
                        report["images_verified" if kind == "image" else "videos_verified"] += 1
                report["failures"] = dict(Counter(item.get("failure", {}).get("code", "unclassified")
                    for item in processed if item.get("download_status") != "downloaded"
                    or item.get("processing_status") != "complete"))
                if options["publish_ready"]:
                    publication = publish_ready_products(apply=True)
                    report["published_products"] = publication["published_products"]
                    report["blocked_products"] = len(publication["blocked_products"])
            report["purchasable_products"] = len(services.get_products())
            if options["report"]:
                atomic_write(Path(options["report"]), encode(report))
            self.stdout.write(json.dumps(report, ensure_ascii=True))
            if report["failures"]:
                raise CommandError("Mídias pendentes; consulte os códigos de diagnóstico. Nenhuma restrição foi contornada.")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
