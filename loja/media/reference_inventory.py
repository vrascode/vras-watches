"""Media provenance is separate from download, optimization and publication."""
import csv
import hashlib
import io
import re
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit, urlunsplit, parse_qsl, urlencode

from django.utils.text import slugify

from loja.media.public_download import validate_public_url


RIGHTS = {
    "status": "owner_authorized_unverified_rightsholder",
    "record": "Proprietário da VRAS autorizou download e uso comercial nesta solicitação em 2026-11-10.",
    "rightsholder_verified": False,
}


def inventory_item(url, model, variant=None, *, kind="image", resolution=None, role="product"):
    validate_public_url(url, resolve=False)
    observed_url = url
    if kind == "image":
        parsed = urlsplit(url)
        query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
                 if key not in {"width", "height", "crop", "format"}]
        url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), ""))
    filename = PurePosixPath(unquote(urlsplit(url).path)).name
    digest = hashlib.sha256(url.encode()).hexdigest()[:16]
    return {"id": digest, "original_url": url, "observed_urls": [observed_url], "filename": filename, "product": model,
            "variant": variant, "type": kind, "role": role, "resolution": resolution,
            "resolution_status": "source_declared" if resolution else "pending_file_inspection",
            "commercial_authorization": RIGHTS.copy(), "download_status": "pending",
            "sha256": None, "original_path": None, "optimized_paths": []}


def discover_inventory(observation):
    result = {}
    variants = observation["variants"]
    by_image = {}
    for variant in variants:
        if variant.get("featured_image_id"):
            by_image.setdefault(variant["featured_image_id"], []).append(variant["title"])
    def add(url, **kwargs):
        if url.startswith("//"):
            url = "https:" + url
        item = inventory_item(url, observation["model"], **kwargs)
        existing = result.setdefault(item["id"], item)
        existing["observed_urls"] = sorted(set(existing["observed_urls"] + item["observed_urls"]))
    for media in observation.get("media", []):
        kind = media.get("media_type")
        matching = by_image.get(media.get("id"), [])
        variant = matching[0] if len(matching) == 1 else None
        resolution = {"width": media["width"], "height": media["height"]} if media.get("width") and media.get("height") else None
        if kind == "image":
            add(media["src"], variant=variant, resolution=resolution)
        elif kind == "video":
            for source in media.get("sources", []):
                if source.get("format") in {"mp4", "webm"}:
                    add(source["url"], variant=None, kind="video",
                        resolution={"width": source.get("width"), "height": source.get("height")})
    for url in observation.get("description_media", []):
        suffix = PurePosixPath(urlsplit(url).path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".avif", ".mp4", ".webm"}:
            add(url, kind="video" if suffix in {".mp4", ".webm"} else "image", role="editorial")
    for url in observation.get("page_media", []):
        suffix = PurePosixPath(urlsplit(url).path).suffix.lower()
        add(url, kind="video" if suffix in {".mp4", ".webm"} else "image", role="page_unassigned")
    return list(result.values())


def relative_original_path(item):
    # Keep the original basename intact, inside a hash folder to avoid collisions.
    if not isinstance(item.get("id"), str) or not re.fullmatch(r"[a-f0-9]{16}", item["id"]):
        raise ValueError("Identificador de mídia inválido.")
    filename = item["filename"]
    if not filename or filename in {".", ".."} or "/" in filename or "\\" in filename or ":" in filename:
        raise ValueError("Nome de arquivo original inválido.")
    return PurePosixPath("media-originals", slugify(item["product"]),
                         slugify(item.get("variant") or "sem-variante-confirmada"), item["id"], filename)


def csv_inventory(items):
    output = io.StringIO(newline="")
    fields = ["original_url", "filename", "product", "variant", "type", "resolution",
              "commercial_authorization", "download_status", "sha256", "original_path"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        row = {field: str(item.get(field) or "") for field in fields}
        # CSV opened in spreadsheet applications must not evaluate remote filenames.
        writer.writerow({key: "'" + value if value.startswith(("=", "+", "-", "@")) else value
                         for key, value in row.items()})
    return output.getvalue()
