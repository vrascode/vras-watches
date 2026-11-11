"""Presentation of imported commercial models, including offers not yet available."""
from urllib.parse import quote

from loja.catalog import services


SWATCHES = {"Prata": "#bbc4cd", "Preto": "#20242b", "Azul": "#23518a", "Verde": "#2b6458",
            "Branco": "#e9e6df", "Dourado": "#c8a668", "Rosé": "#b98273", "Roxo": "#755b9c"}


def model_slug(model):
    from django.utils.text import slugify
    return slugify(model)


def showcase_products():
    from loja.catalog.preview_photos import photo_index, with_preview_photos
    photos = photo_index()
    return [with_preview_photos(p, photos) for p in services.get_products(include_drafts=True)
            if p.get("reference_import")]


def model_groups(products=None):
    groups = {}
    for product in showcase_products() if products is None else products:
        groups.setdefault(product["modelo"], []).append(product)
    return groups


def present_product(product, siblings):
    result = product.copy()
    result["display_price"] = bool(product.get("aprovacao_preco", {}).get("aprovado"))
    result["brand_name"] = product.get("marca", "Poedagar")
    result["selected_color"] = (product.get("verified_variant") or {}).get("cor") or product.get("reference_color", "")
    result["variant_options"] = []
    for sibling in siblings:
        color = (sibling.get("verified_variant") or {}).get("cor") or sibling.get("reference_color", "")
        swatch = next((value for name, value in SWATCHES.items() if name.casefold() in color.casefold()), "#888888")
        result["variant_options"].append({
            "id": sibling["id"], "label": color, "selected": sibling["id"] == product["id"],
            "swatch": swatch, "price": sibling["preco_brl"], "cover": sibling["cover"],
            "url": "/produto/" + str(sibling["id"]) + "/" if sibling["can_purchase"] else
                   "/colecao/" + model_slug(sibling["modelo"]) + "/?cor=" + quote(color),
        })
    result["key_specs"] = [{"label": key, "value": value} for key, value in result["specifications"].items()
                           if key in {"Movimento", "Diâmetro da caixa", "Resistência à água", "Peso"}][:4]
    result["is_reference_showcase"] = not result["can_purchase"]
    return result


def related_models(product, products=None, *, limit=4):
    choices = services.get_products() if products is None else products
    seen = {product.get("modelo") or ("id", product["id"])}
    result = []
    for candidate in sorted(choices, key=lambda p: (p["categoria"] != product["categoria"], not p.get("destaque"))):
        identity = candidate.get("modelo") or ("id", candidate["id"])
        if identity in seen or candidate["id"] == product["id"]:
            continue
        seen.add(identity)
        result.append(candidate)
        if len(result) == limit:
            break
    return result

def reference_cards(query="", category="", sort="destaques"):
    from loja.utils import normalize
    from decimal import Decimal
    if category and normalize(category) != "poedagar":
        return []
    cards = []
    for model, products in model_groups().items():
        if query and normalize(query) not in normalize(model + " " + products[0]["descricao"]):
            continue
        # Published models already appear in the regular storefront.
        if any(product["can_purchase"] for product in products):
            continue
        product = products[0].copy()
        product["showcase_url"] = "/colecao/" + model_slug(model) + "/"
        product["color_count"] = len(products)
        cards.append(product)
    if sort in {"preco_asc", "preco_desc"}:
        cards.sort(key=lambda p: Decimal(str(p["preco"])), reverse=sort == "preco_desc")
    elif sort in {"nome", "nome_desc"}:
        cards.sort(key=lambda p: normalize(p["modelo"]), reverse=sort == "nome_desc")
    return cards
