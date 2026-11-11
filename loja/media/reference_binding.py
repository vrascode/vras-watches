"""Attach only explicitly identified product/variant media, leaving shared assets for review."""
import copy
import json

from loja.catalog import repository
from loja.catalog.reference_storage import atomic_write, catalog_lock, encode
from loja.media import assets as media


def bind_media(items):
    with catalog_lock():
        catalog = repository.load_products()
        original = media.MEDIA_PATH.read_bytes()
        manifest = json.loads(original)
        attached = []
        for item in items:
            if (item.get("download_status") != "downloaded" or item.get("processing_status") != "complete"
                    or not item.get("asset") or not item.get("variant")):
                continue
            if item.get("type") not in {"image", "video"} or not media.local_asset(item["asset"], item["type"]):
                continue
            matches = [p for p in catalog if p.get("reference_import") and p["modelo"] == item["product"]
                       and p.get("reference_color") == item["variant"]]
            if len(matches) != 1:
                continue
            product = matches[0]
            source_id = product["variantes_fonte"][0]["source_sku_id"]
            asset = copy.deepcopy(item["asset"])
            metadata = {"produto_id": product["id"], "catalog_generation": product["catalog_generation"],
                        "modelo": product["modelo"], "source_variant_id": source_id,
                        "import_id": "reference-" + item["id"]}
            asset.update(metadata)
            if item["type"] == "video":
                asset["poster"].update(metadata)
            group = manifest.setdefault("products", {}).setdefault(str(product["id"]), {})
            field = "videos" if item["type"] == "video" else "images"
            collection = group.setdefault(field, [])
            previous = next((i for i, value in enumerate(collection) if value.get("import_id") == asset["import_id"]), None)
            if previous is None:
                collection.append(asset)
            else:
                collection[previous] = asset
            attached.append(item["id"])
        if attached:
            atomic_write(media.MEDIA_PATH, encode(manifest), expected=original)
        return attached
