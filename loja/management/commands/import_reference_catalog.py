"""Import cached observations or refresh the public reference with an explicit mode."""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja.catalog.reference_import import import_observations
from loja.catalog.reference_storage import atomic_write, encode
from loja.catalog.shopify_source import discover_urls, fetch_product
from loja.media.reference_inventory import discover_inventory, csv_inventory
from loja.media.reference_pipeline import import_inventory


class Command(BaseCommand):
    help = "Importação incremental Poedagar. Simula por padrão; --apply grava, --refresh consulta a origem pública."

    def add_arguments(self, parser):
        parser.add_argument("--source", default=str(settings.BASE_DIR / "data/reference_catalog.json"))
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--refresh", action="store_true")
        parser.add_argument("--discover", action="store_true")
        parser.add_argument("--download-media", action="store_true")
        parser.add_argument("--publish-ready", action="store_true")
        parser.add_argument("--url", action="append")
        parser.add_argument("--model")
        parser.add_argument("--max-pages", type=int, default=10)

    def handle(self, *args, **options):
        try:
            if options["publish_ready"] and not options["apply"]:
                raise ValueError("--publish-ready exige --apply.")
            if options["max_pages"] < 1 or options["max_pages"] > 100:
                raise ValueError("--max-pages deve estar entre 1 e 100.")
            if options["download_media"] and not options["apply"]:
                raise ValueError("--download-media exige --apply; a simulação não baixa arquivos.")
            source = Path(options["source"])
            if options["refresh"]:
                urls = discover_urls(max_pages=options["max_pages"]) if options["discover"] else options["url"]
                if not urls:
                    raise ValueError("Informe --url ou --discover com --refresh.")
                observations = [fetch_product(url)[0] for url in urls]
                if options["apply"]:
                    atomic_write(source, encode({"schema_version": 1, "products": observations}))
            else:
                if options["discover"] or options["url"]:
                    raise ValueError("--url e --discover exigem --refresh.")
                observations = json.loads(source.read_text(encoding="utf-8"))["products"]
            if options["model"]:
                observations = [p for p in observations if p["model"].casefold() == options["model"].casefold()]
                if not observations:
                    raise ValueError("Modelo não encontrado.")
            report = import_observations(observations, apply=options["apply"])
            if options["download_media"]:
                inventory_path = settings.BASE_DIR / "data/reference_media_inventory.json"
                old = json.loads(inventory_path.read_text(encoding="utf-8")) if inventory_path.exists() else {"items": []}
                indexed = {item["id"]: item for item in old["items"]}
                current = []
                for observation in observations:
                    for item in discover_inventory(observation):
                        current.append(indexed.get(item["id"], item))
                if not options["refresh"] and not current:
                    current = [i for i in old["items"] if i["product"] in {p["model"] for p in observations}]
                processed = import_inventory(current)
                indexed.update({item["id"]: item for item in processed})
                items = list(indexed.values())
                atomic_write(inventory_path, encode({**old, "schema_version": 1, "items": items}))
                atomic_write(settings.BASE_DIR / "data/reference_media_inventory.csv", csv_inventory(items).encode("utf-8-sig"))
                from loja.media.reference_binding import bind_media
                report["media_attached"] = len(bind_media(processed))
                report["downloaded"] = sum(i["download_status"] == "downloaded" for i in processed)
                report["media_errors"] = sum(i["download_status"] == "error" or i.get("processing_status") == "error" for i in processed)
            if options["publish_ready"]:
                from loja.catalog.publication import publish_ready_products
                report["publication"] = publish_ready_products(apply=True)
            self.stdout.write(json.dumps(report, ensure_ascii=True))
            if report.get("media_errors"):
                raise CommandError("Algumas mídias não foram baixadas. Consulte o inventário e execute novamente.")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
