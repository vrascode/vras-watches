"""Reference photos for presentation only; never evidence for sale publication."""
import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings

from loja.media.public_download import validate_public_url


def photo_index():
    path = settings.BASE_DIR / "data/reference_media_inventory.json"
    try:
        inventory = json.loads(path.read_bytes())
    except (OSError, ValueError):
        return {}
    indexed = {}
    for item in inventory.get("items", []):
        if item.get("type") != "image" or item.get("role") != "product" or not item.get("variant"):
            continue
        try:
            url = validate_public_url(item["original_url"], resolve=False)
        except (KeyError, ValueError):
            continue
        parsed = urlsplit(url)
        query = [(key, value) for key, value in parse_qsl(parsed.query) if key != "width"]
        display = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query + [("width", "1000")]), ""))
        indexed.setdefault((item["product"], item["variant"]), []).append({
            "url": display, "original_url": url, "external": True,
            "alt": f"Poedagar {item['product']} — {item['variant']}",
            "source_page": item.get("source_page") or "https://poedagareco.com",
        })
    return indexed


def with_preview_photos(product, indexed):
    result = product.copy()
    # Source URLs never satisfy sale publication or enter the commercial manifest.
    if not result.get("reference_import") or result["can_purchase"] or result.get("gallery_items"):
        return result
    photos = indexed.get((result["modelo"], result.get("reference_color")), [])
    if photos:
        result["cover"] = photos[0]
        result["gallery_items"] = [{"image": photo, "video": None} for photo in photos]
        result["external_photo_source"] = photos[0]["source_page"]
    return result
