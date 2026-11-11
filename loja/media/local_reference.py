"""Offline validation, receipts and status for Windows-downloaded originals."""
import argparse
import hashlib
import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

from PIL import Image

from loja.catalog.reference_storage import atomic_write, encode
from loja.media.public_download import validate_public_url
from loja.media.reference_inventory import relative_original_path

MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 40_000_000
FORMATS = {"JPEG", "PNG", "WEBP", "AVIF"}
FILE_ERRORS = (OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning)


def authorized_image(item):
    """Recorded owner permission is distinct from verified third-party ownership."""
    authorization = item.get("commercial_authorization") or {}
    return (item.get("type") == "image" and isinstance(authorization, dict)
            and bool(str(authorization.get("record") or "").strip())
            and authorization.get("status") not in {"revoked", "denied", "rejected"}
            and authorization.get("revoked") is not True
            and authorization.get("confirmed") is not False
            and (authorization.get("confirmed") is True
                 or authorization.get("status") == "owner_authorized_unverified_rightsholder"))


def inventory_at(root):
    return json.loads((Path(root) / "data/reference_media_inventory.json").read_bytes())


def unique_items(inventory):
    indexed = {}
    for item in inventory["items"]:
        key = item["id"]
        if key in indexed and item != indexed[key]:
            raise ValueError(f"Conflicting duplicate media ID: {key}")
        indexed[key] = item
    return list(indexed.values())


def storage_root(root):
    root = Path(root).resolve()
    storage = (root / "media-originals").resolve()
    if not storage.is_relative_to(root):
        raise ValueError("Originals directory resolves outside the project.")
    return storage


def original_path(root, item):
    validate_public_url(item["original_url"], resolve=False)
    if hashlib.sha256(item["original_url"].encode()).hexdigest()[:16] != item["id"]:
        raise ValueError("Media ID does not match the original URL.")
    relative = relative_original_path(item)
    filename = item["filename"]
    if PureWindowsPath(filename).is_reserved() or filename.rstrip(" .") != filename:
        raise ValueError("Invalid original filename on Windows.")
    target = Path(root).resolve().joinpath(*relative.parts).resolve()
    if not target.is_relative_to(storage_root(root)):
        raise ValueError("Original resolves outside the media directory.")
    return target


def inspect_image(path):
    path = Path(path)
    size = path.stat().st_size
    if not 0 < size <= MAX_BYTES:
        raise ValueError(f"Image must contain 1..{MAX_BYTES} bytes.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as photo:
            if photo.format not in FORMATS:
                raise ValueError(f"Unsupported image format: {photo.format}")
            if photo.width * photo.height > MAX_PIXELS:
                raise ValueError("Image exceeds 40 megapixels.")
            if getattr(photo, "n_frames", 1) != 1:
                raise ValueError("Animated images require manual review.")
            details = {"format": photo.format, "bytes": size,
                       "resolution": {"width": photo.width, "height": photo.height}}
            photo.verify()
        with Image.open(path) as photo:
            photo.load()
    details["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return details


def receipt_path(root, item):
    original_path(root, item)
    path = (storage_root(root) / ".receipts" / (item["id"] + ".json")).resolve()
    if not path.is_relative_to(storage_root(root)):
        raise ValueError("Receipt resolves outside the media directory.")
    return path


def read_receipt(root, item):
    path = receipt_path(root, item)
    if not path.is_file():
        return {}
    receipt = json.loads(path.read_bytes())
    if receipt.get("id") != item["id"] or receipt.get("original_url") != item["original_url"]:
        raise ValueError("Receipt does not belong to this original URL.")
    return receipt


def verify_expected_hashes(root, item, details):
    receipt = read_receipt(root, item)
    for expected in (item.get("sha256"), receipt.get("sha256")):
        if expected and expected != details["sha256"]:
            raise ValueError("Preserved original hash differs; file will not be overwritten.")


def inspect_original(root, item):
    details = inspect_image(original_path(root, item))
    verify_expected_hashes(root, item, details)
    return details


def record_original(root, item, details, *, transferred=False):
    receipt = read_receipt(root, item)
    receipt.update(id=item["id"], original_url=item["original_url"],
                   original_path=relative_original_path(item).as_posix(),
                   status="validated", validated_at=datetime.now(timezone.utc).isoformat(),
                   last_error=None, **details)
    if transferred:
        receipt["downloaded_at"] = datetime.now(timezone.utc).isoformat()
        receipt["transport"] = "PowerShell Invoke-WebRequest"
    atomic_write(receipt_path(root, item), encode(receipt))
    return receipt


def finalize_download(root, item, candidate):
    if not authorized_image(item):
        raise ValueError("No recorded commercial authorization for this image.")
    candidate = Path(candidate).resolve()
    incoming = (storage_root(root) / ".incoming").resolve()
    if not incoming.is_relative_to(storage_root(root)) or not candidate.is_relative_to(incoming):
        raise ValueError("Download candidate is outside the staging directory.")
    details = inspect_image(candidate)
    verify_expected_hashes(root, item, details)
    destination = original_path(root, item)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        previous = inspect_original(root, item)
        if previous["sha256"] != details["sha256"]:
            raise ValueError("An original already exists with different contents.")
        return record_original(root, item, previous)
    # Atomic same-volume creation fails if another process creates the original.
    os.link(candidate, destination)
    return record_original(root, item, details, transferred=True)


def download_plan(root):
    inventory = inventory_at(root)
    storage = storage_root(root)
    incoming = (storage / ".incoming").resolve()
    lock_path = (storage / ".powershell-download.lock").resolve()
    if not incoming.is_relative_to(storage) or not lock_path.is_relative_to(storage):
        raise ValueError("Staging or lock path resolves outside the media directory.")
    entries = []
    for item in unique_items(inventory):
        entry = {"id": item["id"], "url": item["original_url"], "product": item["product"],
                 "variant": item.get("variant"), "authorized": authorized_image(item)}
        if not entry["authorized"]:
            entry.update(action="skip", reason="commercial_authorization_missing")
        else:
            try:
                path = original_path(root, item)
                entry["destination"] = str(path)
                if path.exists():
                    inspect_original(root, item)
                    entry["action"] = "reuse"
                else:
                    entry["action"] = "download"
            except FILE_ERRORS as error:
                entry.update(action="error", reason=str(error))
        entries.append(entry)
    return {"urls_identified": len({i["original_url"] for i in inventory["items"]}),
            "images_authorized": sum(e["authorized"] for e in entries),
            "storage_directory": str(storage), "incoming_directory": str(incoming), "lock_path": str(lock_path),
            "authorization_basis": "recorded_owner_authorization; not verified third-party ownership",
            "items": entries}


def gallery_ids(root):
    root = Path(root).resolve()
    manifest_path = root / "data/media.json"
    if not manifest_path.is_file():
        return {}, set()
    catalog = {str(p["id"]): p for p in json.loads((root / "data/products.json").read_bytes())}
    groups = json.loads(manifest_path.read_bytes()).get("products", {})
    imports, products = {}, set()
    for product_id, group in groups.items():
        if product_id not in catalog:
            continue
        for entry in group.get("images", []):
            if entry.get("autorizado") is not True or not entry.get("origem"):
                continue
            src = entry.get("src", "")
            if not src or "\\" in src or ":" in src:
                continue
            target = (root / "static" / src).resolve()
            if not target.is_relative_to(root / "static"):
                continue
            try:
                inspect_image(target)
            except FILE_ERRORS:
                continue
            products.add(product_id)
            imports[entry.get("import_id")] = product_id
    return imports, products


def media_status(root):
    items = unique_items(inventory_at(root))
    imports, products = gallery_ids(root)
    catalog = {str(p["id"]): p for p in json.loads((Path(root) / "data/products.json").read_bytes())}
    download_errors = {}
    valid, completed, associated, errors = [], [], [], {}
    for item in items:
        try:
            inspect_original(root, item)
            valid.append(item["id"])
            if read_receipt(root, item).get("downloaded_at") or item.get("download_status") == "downloaded":
                completed.append(item["id"])
            target = catalog.get(imports.get("reference-" + item["id"]), {})
            if (authorized_image(item) and item.get("variant") and item.get("processing_status") == "complete"
                    and target.get("reference_import") and target.get("modelo") == item["product"]
                    and target.get("reference_color") == item["variant"]):
                associated.append(item["id"])
        except FILE_ERRORS as error:
            errors[item["id"]] = str(error)
        try:
            receipt_error = read_receipt(root, item).get("last_error")
            if receipt_error:
                download_errors[item["id"]] = receipt_error
        except FILE_ERRORS:
            pass
    return {"urls_identified": len({i["original_url"] for i in items}),
            "images_authorized": sum(authorized_image(i) for i in items),
            "rightsholder_verified": sum((i.get("commercial_authorization") or {}).get("rightsholder_verified") is True for i in items),
            "downloads_completed": len(completed), "valid_images": len(valid),
            "products_with_gallery": len(products), "media_pending": len(items) - len(associated),
            "download_pending": sum(authorized_image(i) and i["id"] not in valid for i in items),
            "unassigned_images": sum(not i.get("variant") for i in items),
            "media_associated": len(associated), "file_errors": errors, "download_errors": download_errors,
            "complete": len(associated) == len(items)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("action", choices=["plan", "reuse", "finalize", "failure", "report"])
    parser.add_argument("--id")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--message")
    options = parser.parse_args(argv)
    try:
        if options.action == "plan":
            result = download_plan(options.root)
        elif options.action == "report":
            result = media_status(options.root)
            atomic_write(options.root / "artifacts/catalogos/poedagar/powershell-download-report.json", encode(result))
        else:
            item = next(i for i in unique_items(inventory_at(options.root)) if i["id"] == options.id)
            if not authorized_image(item):
                raise ValueError("Image lacks recorded commercial authorization.")
            if options.action == "finalize":
                result = finalize_download(options.root, item, options.candidate)
            elif options.action == "reuse":
                result = record_original(options.root, item, inspect_original(options.root, item))
            else:
                result = read_receipt(options.root, item)
                result.update(id=item["id"], original_url=item["original_url"],
                              last_error=options.message, last_attempt_at=datetime.now(timezone.utc).isoformat())
                atomic_write(receipt_path(options.root, item), encode(result))
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except FILE_ERRORS + (KeyError, StopIteration) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=True))
        return 1
