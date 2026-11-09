"""Published catalog queries, variant navigation and gallery composition."""
from decimal import Decimal

from loja.catalog import repository, validation
from loja.media import assets as media
from loja.utils import format_brl, normalize


CATEGORY_LABELS = {"Classicos": "Cl\u00e1ssicos", "Lancamentos": "Lan\u00e7amentos", "Best Sellers": "Seleção VRAS"}
SORT_OPTIONS = {"destaques": "Destaques", "preco_asc": "Menor pre\u00e7o",
                "preco_desc": "Maior pre\u00e7o", "nome": "Nome: A a Z", "nome_desc": "Nome: Z a A"}


def get_products(include_drafts=False):
    manifest = media.load_media()
    raw = repository.load_products(decimal_prices=True)
    products = [_prepare_product(item, manifest) for item in raw]
    visible = [p for p in products if p["can_purchase"]]
    _attach_variant_options(products, visible)
    return products if include_drafts else visible


def catalog_generation():
    raw = repository.load_products()
    generations = {p.get("catalog_generation", "legacy") for p in raw}
    return next(iter(generations)) if len(generations) == 1 else "mixed-invalid"


def is_retired_product(product_id):
    return catalog_generation() == "poedagar-v1" and product_id in range(1, 13)


def get_featured_products(catalog=None):
    return [product for product in (get_products() if catalog is None else catalog) if product.get("destaque")]


def get_new_products(catalog=None):
    return [product for product in (get_products() if catalog is None else catalog) if product["is_new"]]


def get_style_edits(catalog=None):
    catalog = get_products() if catalog is None else catalog
    return [{"category": category, "label": CATEGORY_LABELS.get(category, category), "title": title,
             "description": description, "products": [p for p in catalog if p["categoria"] == category][:2]}
            for category, title, description in [
                ("Classicos", "Elegância em cada detalhe.", "Linhas clássicas para compor o seu estilo, no seu tempo."),
                ("Esportivos", "Presença para cada ritmo.", "Um olhar esportivo para acompanhar suas escolhas do dia a dia."),
            ] if any(p["categoria"] == category for p in catalog)]


def get_product(product_id):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return None
    return next((product for product in get_products() if product["id"] == product_id), None)


def get_categories():
    return sorted({product["categoria"] for product in get_products()})


def get_collections(catalog=None):
    catalog = get_products() if catalog is None else catalog
    return [{"name": category, "label": CATEGORY_LABELS.get(category, category),
             "count": sum(product["categoria"] == category for product in catalog),
             "cover": next((product["cover"] for product in catalog
                            if product["categoria"] == category and product["cover"]), None)}
            for category in sorted({p["categoria"] for p in catalog})]


def filter_products(category=None, query=None, sort="destaques"):
    products = get_products()
    if category:
        products = [p for p in products if normalize(p["categoria"]) == normalize(category)]
    if query:
        search = normalize(query)
        products = [p for p in products if search in normalize(
            " ".join([p["nome"], p["descricao"], p["categoria"]]
                     + [p["verified_identity"][key] for key in ("marca", "modelo", "referencia")
                        if p["verified_identity"]]
                     + [p["verified_variant"][key] for key in ("cor", "pulseira")
                        if p["verified_variant"]]))]
    if sort in {"preco_asc", "preco_desc"}:
        return sorted(products, key=lambda p: p["preco"], reverse=sort == "preco_desc")
    if sort in {"nome", "nome_desc"}:
        return sorted(products, key=lambda p: normalize(p["nome"]), reverse=sort == "nome_desc")
    return sorted(products, key=lambda p: not p.get("destaque", False))


def _prepare_product(item: dict, manifest: dict) -> dict:
    product = item.copy()
    product["preco"] = Decimal(str(product["preco"])) if product.get("preco") is not None else None
    product["preco_brl"] = format_brl(product["preco"]) if product["preco"] is not None else ""
    product["category_label"] = CATEGORY_LABELS.get(product["categoria"], product["categoria"])
    product["is_new"] = normalize(product["categoria"]) == "lancamentos"
    _attach_gallery(product, manifest)
    identity = product.get("identificacao", {})
    product["verified_identity"] = identity if validation.verified_record(
        identity, ("marca", "modelo", "referencia", "fonte")) else None
    variant = product.get("variante", {})
    product["verified_variant"] = variant if product["verified_identity"] and validation.verified_record(
        variant, ("cor", "pulseira", "fonte")) else None
    product["specifications"] = {
        label: entry["valor"] for label, entry in product.get("especificacoes", {}).items()
        if validation.verified_record(entry, ("valor", "fonte"))
    }
    product["publication_issues"] = validation.publication_issues(product)
    product["can_purchase"] = not product["publication_issues"]
    return product


def _attach_gallery(product: dict, manifest: dict) -> None:
    """Resolve only authorized local media, preserving cover and gallery order."""
    product_media = manifest.get("products", {}).get(str(product["id"]), {})
    # Legacy filenames are preserved, but are not proof of authorization.
    images = product_media.get("images", product.get("galeria", []))
    videos = product_media.get("videos", product.get("videos", []))
    product["images"] = [asset for entry in images if (asset := media.local_asset(entry))]
    product["videos"] = [asset for entry in videos if (asset := media.local_asset(entry, "video"))]
    product["cover"] = media.local_asset(product_media.get("cover", product.get("capa")))
    if not product["cover"]:
        product["cover"] = next(iter(product["images"]), None)
    if not product["cover"] and product["videos"]:
        product["cover"] = product["videos"][0]["poster"]
    if product["cover"] and product["cover"] not in product["images"]:
        product["images"].insert(0, product["cover"])
    product["secondary_image"] = product["images"][1] if len(product["images"]) > 1 else None
    product["preview_video"] = next(iter(product["videos"]), None)
    product["gallery_items"] = ([{"image": asset, "video": None} for asset in product["images"]]
                                + [{"image": asset["poster"], "video": asset} for asset in product["videos"]])


def _attach_variant_options(products: list[dict], visible: list[dict]) -> None:
    # Each confirmed color/strap combination has its own existing product ID and cart line.
    # Navigation works without JavaScript and never borrows the current product's price/media.
    for product in products:
        product["variant_options"] = []
        identity = product["verified_identity"]
        if not identity or not product["verified_variant"]:
            continue
        group = tuple(normalize(identity[key]) for key in ("marca", "modelo", "referencia"))
        for candidate in visible:
            other = candidate["verified_identity"]
            variant = candidate["verified_variant"]
            if other and variant and group == tuple(normalize(other[key]) for key in ("marca", "modelo", "referencia")):
                product["variant_options"].append({
                    "id": candidate["id"], "label": f"{variant['cor']} / {variant['pulseira']}",
                    "selected": candidate["id"] == product["id"],
                })
