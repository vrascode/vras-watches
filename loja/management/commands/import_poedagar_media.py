"""Import only validated local originals. This command has no network transport."""
import copy
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja.catalog.reference_storage import atomic_write, catalog_lock, encode
from loja.media.local_reference import (FILE_ERRORS, authorized_image, inspect_original,
                                        media_status, record_original, unique_items)
from loja.media.reference_binding import bind_media
from loja.media.reference_inventory import csv_inventory, relative_original_path
from loja.media.reference_pipeline import import_inventory


def refuse_network(url):
    raise OSError("Local-only import: network downloads are disabled.")


class Command(BaseCommand):
    help = "Importa imagens locais baixadas pelo PowerShell; nunca baixa ou publica ofertas."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--report", default=str(settings.BASE_DIR / "artifacts/catalogos/poedagar/local-import-report.json"))

    def handle(self, *args, **options):
        root = settings.BASE_DIR
        try:
            path = root / "data/reference_media_inventory.json"
            original = path.read_bytes()
            inventory = json.loads(original)
            items = unique_items(inventory)
            errors, selected, unassigned = {}, [], []
            for item in items:
                if not authorized_image(item):
                    continue
                try:
                    details = inspect_original(root, item)
                    entry = copy.deepcopy(item)
                    entry.update(sha256=details["sha256"],
                                 original_path=relative_original_path(item).as_posix(),
                                 download_status="downloaded")
                    selected.append(entry)
                    if not entry.get("variant"):
                        unassigned.append(entry["id"])
                except FILE_ERRORS as error:
                    errors[item["id"]] = str(error)
            attached, processed = [], []
            if options["apply"]:
                # Every selected original has a hash and is already on disk.
                # If it disappears mid-import, the injected fetch refuses any network.
                processed = import_inventory(selected, root=root, fetch=refuse_network)
                indexed = {item["id"]: item for item in processed}
                updated = {**inventory, "items": [indexed.get(item["id"], item) for item in inventory["items"]]}
                with catalog_lock():
                    atomic_write(path, encode(updated), expected=original)
                    atomic_write(root / "data/reference_media_inventory.csv",
                                 csv_inventory(updated["items"]).encode("utf-8-sig"))
                for item in processed:
                    if item.get("download_status") == "downloaded":
                        record_original(root, item, inspect_original(root, item))
                attached = bind_media(processed)
            report = media_status(root)
            report.update(applied=options["apply"], eligible_local_images=len(selected),
                          imported_images=sum(i.get("processing_status") == "complete" for i in processed),
                          media_attached=len(attached), missing_or_invalid_originals=errors,
                          import_failures={i["id"]: i.get("error") for i in processed if i.get("processing_status") != "complete"},
                          unassigned_image_ids=unassigned, published_products=[])
            atomic_write(Path(options["report"]), encode(report))
            self.stdout.write(json.dumps(report, ensure_ascii=True))
            if options["apply"] and (errors or report["import_failures"]):
                raise CommandError("Some authorized originals are missing or invalid. See the local import report.")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CommandError(str(error)) from error
