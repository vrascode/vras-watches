"""Read Shopify's public product JSON; no storefront code or marketing copy reuse."""
import json
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit

from loja.media.public_download import validate_public_url

from loja.catalog.reference_schema import source_url, validate_observation
from loja.media.public_download import download


class ProductHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.media = set()
        self.specifications = {}
        self._li = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "li":
            self._li = []
        if tag in {"img", "source", "video"}:
            for key in ("src", "data-src", "poster"):
                value = attrs.get(key)
                if value:
                    self.media.add(urljoin("https://poedagareco.com", value))
            for candidate in attrs.get("srcset", "").split(","):
                if candidate.strip():
                    self.media.add(urljoin("https://poedagareco.com", candidate.strip().split()[0]))

    def handle_data(self, data):
        if self._li is not None:
            self._li.append(data)

    def handle_endtag(self, tag):
        if tag == "li" and self._li is not None:
            text = unescape(" ".join(self._li)).strip()
            if ":" in text:
                label, value = text.split(":", 1)
                if 0 < len(label.strip()) <= 60 and 0 < len(value.strip()) <= 300:
                    self.specifications[label.strip()] = value.strip()
            self._li = None


def normalize_product(raw, url):
    source_url(url)
    if not isinstance(raw, dict) or not raw.get("variants"):
        raise ValueError("Resposta de produto Shopify inválida.")
    title = raw.get("title", "")
    if "poedagar" not in title.casefold() or not title.casefold().startswith("relógio"):
        raise ValueError("A origem não identifica um relógio Poedagar.")
    model = re.sub(r"^Relógio\s+Poedagar\s+", "", title, flags=re.I).replace("®", "").strip()
    parser = ProductHTML()
    parser.feed(raw.get("description", ""))
    variants = []
    for variant in raw["variants"]:
        cents = variant.get("price")
        if type(cents) is not int or cents <= 0:
            raise ValueError("O preço público deve ser inteiro em centavos.")
        variants.append({"title": variant["title"], "source_id": variant["id"],
                         "price_brl": f"{cents // 100}.{cents % 100:02d}",
                         "available": variant.get("available"),
                         "featured_image_id": (variant.get("featured_image") or {}).get("id")})
    result = {"brand": "Poedagar", "model": model, "name": title, "url": url,
              "checked_at": datetime.now(timezone.utc).isoformat(), "price_brl": variants[0]["price_brl"],
              "description": f"{model}: um relógio Poedagar selecionado pela VRAS Watches para acompanhar o seu estilo.",
              "variants": variants, "specifications": parser.specifications,
              "media": raw.get("media", []), "description_media": sorted(parser.media),
              "source_product_id": raw.get("id"), "completeness": "public_product_json"}
    return validate_observation(result)


def fetch_product(url):
    source_url(url)
    content, _ = download(url.rstrip("/") + ".js", limit=8 * 1024 * 1024)
    raw = json.loads(content)
    observation = normalize_product(raw, url)
    # The full page can contain theme videos and editorial images absent from .js.
    page, _ = download(url, limit=16 * 1024 * 1024)
    parser = ProductHTML()
    markup = page.decode("utf-8")
    parser.feed(markup)
    candidates = set(parser.media)
    candidates.update(re.findall(r"https://[^\s<>\"']+\.(?:mp4|webm)(?:\?[^\s<>\"']*)?", markup.replace("\\/", "/")))
    observed = []
    for candidate in candidates:
        try:
            candidate = unescape(candidate)
            validate_public_url(candidate, resolve=False)
        except ValueError:
            continue
        if urlsplit(candidate).path.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".avif", ".mp4", ".webm")):
            observed.append(candidate)
    observation["page_media"] = sorted(observed)
    return observation, raw


def discover_urls(*, max_pages=10):
    urls, seen = [], set()
    for page in range(1, max_pages + 1):
        content, _ = download(f"https://poedagareco.com/products.json?limit=250&page={page}", limit=16 * 1024 * 1024)
        products = json.loads(content).get("products")
        if not isinstance(products, list):
            raise ValueError("Lista pública de produtos inválida.")
        if not products:
            return urls
        fresh = 0
        for product in products:
            if "poedagar" not in product.get("title", "").casefold() or not product.get("title", "").casefold().startswith("relógio"):
                continue
            url = "https://poedagareco.com/products/" + quote(product["handle"])
            if url not in seen:
                seen.add(url)
                urls.append(url)
                fresh += 1
        if len(products) < 250 or fresh == 0:
            return urls
    raise ValueError("Limite de páginas atingido; aumente max_pages explicitamente.")
