import json
import unicodedata
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings

from loja import media

PRODUCTS_PATH = settings.BASE_DIR / "data" / "products.json"
CART_SESSION_KEY = "cart"
MAX_QUANTITY = 99
CATEGORY_LABELS = {"Classicos": "Cl\u00e1ssicos", "Lancamentos": "Lan\u00e7amentos", "Best Sellers": "Seleção VRAS"}
SORT_OPTIONS = {"destaques": "Destaques", "preco_asc": "Menor pre\u00e7o",
                "preco_desc": "Maior pre\u00e7o", "nome": "Nome: A a Z", "nome_desc": "Nome: Z a A"}


def normalize(value):
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(char))


def format_brl(value):
    return f"R$ {Decimal(str(value)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def verified_record(record, fields):
    """A supplier listing alone does not establish the identity of a local SKU."""
    if (not isinstance(record, dict) or record.get("confirmada") is not True
            or not all(isinstance(record.get(key), str) and record[key].strip() for key in fields)
            or not isinstance(record.get("fonte"), str)):
        return False
    try:
        origin = urlsplit(record["fonte"])
        return origin.scheme == "https" and bool(origin.hostname) and not origin.username and not origin.password
    except ValueError:
        return False


def get_products():
    manifest = media.load_media()
    with Path(PRODUCTS_PATH).open(encoding="utf-8") as source:
        raw = json.load(source, parse_float=Decimal)
    products = []
    for item in raw:
        product = item.copy()
        product["preco"] = Decimal(str(product["preco"]))
        product["preco_brl"] = format_brl(product["preco"])
        product["category_label"] = CATEGORY_LABELS.get(product["categoria"], product["categoria"])
        product["is_new"] = normalize(product["categoria"]) == "lancamentos"
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
        identity = product.get("identificacao", {})
        product["verified_identity"] = identity if verified_record(
            identity, ("marca", "modelo", "referencia", "fonte")) else None
        variant = product.get("variante", {})
        product["verified_variant"] = variant if product["verified_identity"] and verified_record(
            variant, ("cor", "pulseira", "fonte")) else None
        product["specifications"] = {
            label: entry["valor"] for label, entry in product.get("especificacoes", {}).items()
            if verified_record(entry, ("valor", "fonte"))
        }
        products.append(product)
    # Each confirmed color/strap combination has its own existing product ID and cart line.
    # Navigation works without JavaScript and never borrows the current product's price/media.
    for product in products:
        product["variant_options"] = []
        identity = product["verified_identity"]
        if not identity or not product["verified_variant"]:
            continue
        group = tuple(normalize(identity[key]) for key in ("marca", "modelo", "referencia"))
        for candidate in products:
            other = candidate["verified_identity"]
            variant = candidate["verified_variant"]
            if other and variant and group == tuple(normalize(other[key]) for key in ("marca", "modelo", "referencia")):
                product["variant_options"].append({
                    "id": candidate["id"], "label": f"{variant['cor']} / {variant['pulseira']}",
                    "selected": candidate["id"] == product["id"],
                })
    return products


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
            for category in ["Classicos", "Maestro", "Best Sellers", "Lancamentos", "Esportivos"]]


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


def get_cart(session):
    stored = session.get(CART_SESSION_KEY, {})
    if not isinstance(stored, dict):
        return {}
    valid_ids = {str(p["id"]) for p in get_products()}
    return {str(key): min(value, MAX_QUANTITY) for key, value in stored.items()
            if str(key) in valid_ids and type(value) is int and value > 0}


def cart_count(session):
    return sum(get_cart(session).values())


def set_quantity(session, product_id, quantity):
    if type(quantity) is not int or not 0 <= quantity <= MAX_QUANTITY:
        raise ValueError("Quantidade deve estar entre 0 e 99.")
    if not get_product(product_id):
        raise ValueError("Produto nao encontrado.")
    cart = get_cart(session).copy()
    key = str(product_id)
    if quantity:
        cart[key] = quantity
    else:
        cart.pop(key, None)
    session[CART_SESSION_KEY] = cart
    session.modified = True


def add_to_cart(session, product_id):
    current = get_cart(session).get(str(product_id), 0)
    if current >= MAX_QUANTITY:
        raise ValueError("Limite de 99 unidades por modelo.")
    set_quantity(session, product_id, current + 1)


def remove_from_cart(session, product_id):
    set_quantity(session, product_id, max(0, get_cart(session).get(str(product_id), 0) - 1))


def get_cart_items(session):
    catalog = {str(p["id"]): p for p in get_products()}
    items = []
    for product_id, quantity in get_cart(session).items():
        product = catalog[product_id]
        subtotal = product["preco"] * quantity
        items.append({"product": product, "quantity": quantity, "unit_price": product["preco"],
                      "subtotal": subtotal, "subtotal_brl": format_brl(subtotal)})
    return items


def cart_total(session):
    return sum((item["subtotal"] for item in get_cart_items(session)), Decimal("0.00"))


def cart_summary(session):
    items = get_cart_items(session)
    total = sum((item["subtotal"] for item in items), Decimal("0.00"))
    return {"items": items, "quantity": sum(item["quantity"] for item in items),
            "total": total, "total_brl": format_brl(total)}
