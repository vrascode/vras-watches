"""Read public product metadata for an offline review; never download product photos.

Run explicitly, outside request handling. This cannot change products or published prices.
"""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://lojaspoedagar.com.br"
FIRST = "https://poedagareco.com"
FIRST_CANDIDATES = {
    "deluxe": "relogio-poedagar-deluxe-edition",
    "golden-star": "relogio-poedagar-goldenstar",
    "signature": "relogio-poedagar-signature",
    "king-royal": "poedagar-kingroyal",
    "army": "relogio-poedagar-army",
    "legitimus": "relogio-poedagar-legitimo",
    "relogio-poedagar-nautilus-azul": "relogio-poedagar-nautilus",
    "universy": "relogio-poedagar-universo",
    "machine": "relogio-poedagar-machine",
    "lattitude": "relogio-poedagar-latittude",
}


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "VRAS-catalog-review/1.0"}), timeout=30) as response:
        content = response.read()
        return content.decode("utf-8"), hashlib.sha256(content).hexdigest()


def read_product(path):
    url = SITE + path
    checked = datetime.now(timezone.utc).isoformat()
    try:
        html, sha = fetch(url)
        match = re.search(r"window\.data\s*=\s*", html)
        product = json.JSONDecoder().raw_decode(html[match.end():])[0]["product"]["data"]
        variants = []
        for sku in product["skus"]["data"]:
            prices = sku["prices"]["data"]
            variants.append({
                "source_sku": sku["sku"], "source_sku_id": sku["id"],
                "title": sku["title"], "options": sku["variations"],
                "price_brl": prices["price"],
                "pix_brl": prices.get("pix", {}).get("price"),
                "source_blocked_sale": sku["blocked_sale"],
                "source_stock_status": sku["stock_status"],
                "image_urls_for_review_only": [image["url"] for image in sku["images"]["data"]],
            })
        return {"name": product["name"], "slug": product["slug"], "url": url,
                "checked_at_utc": checked, "html_sha256": sha,
                "method": "public HTML window.data.product.data.skus.data[].prices.data.price",
                "variants": variants, "vras_product_id": None,
                "match_status": "unconfirmed", "price_approval": "not_submitted_no_exact_match"}
    except Exception as error:
        return {"url": url, "checked_at_utc": checked, "error": str(error)}


def read_first(pair):
    slug, handle = pair
    url = FIRST + "/products/" + handle
    checked = datetime.now(timezone.utc).isoformat()
    try:
        html, sha = fetch(url)
        # Read only JSON-LD facts; do not copy marketing text or media files.
        schemas = []
        for content in re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html, re.S):
            try:
                value = json.loads(content)
                if isinstance(value, dict) and value.get("@type") == "Product":
                    schemas.append({k: value[k] for k in ("name", "sku", "mpn", "brand", "image") if k in value})
            except json.JSONDecodeError:
                continue
        # Option labels are taken from the public page's swatch inputs.
        colors = list(dict.fromkeys(re.findall(r'<input[^>]*name="option1"[^>]*value="([^"]+)"', html)))
        return {"second_site_slug_candidate": slug, "url": url, "checked_at_utc": checked,
                "html_sha256": sha, "schema_identity": schemas, "option_labels": colors,
                "match_status": "name_candidate_only_requires_reference_and_variant_confirmation",
                "image_reuse_authorized": False}
    except Exception as error:
        return {"url": url, "checked_at_utc": checked, "error": str(error)}


if __name__ == "__main__":
    category, _ = fetch(SITE + "/masculinos?sort_by=best_sellers")
    paths = sorted(set(re.findall(r'href="([^"?]+/p)"', category)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        products = list(pool.map(read_product, paths))
        first = list(pool.map(read_first, FIRST_CANDIDATES.items()))
    report = {"consulted_at_utc": datetime.now(timezone.utc).isoformat(),
              "category_url": SITE + "/masculinos?sort_by=best_sellers",
              "currency": "BRL", "scope": "18 linked men's products; 10 first-site name candidates",
              "prices_are_proposals_only": True, "photographs_downloaded": 0,
              "products": products, "first_site_candidates": first}
    destination = ROOT / "data/poedagar_sources.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"products": len(products), "first_candidates": len(first),
                      "errors": [p for p in products + first if "error" in p]}, ensure_ascii=False))
