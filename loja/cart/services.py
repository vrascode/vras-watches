"""Reconcile published offers with existing session keys and Decimal totals."""
from decimal import Decimal

from loja.catalog import services as catalog_services
from loja.utils import format_brl


CART_SESSION_KEY = "cart"
CART_VERSION_KEY = "cart_catalog_generation"
CART_NOTICE_KEY = "cart_catalog_updated"
CART_OFFERS_KEY = "cart_offer_versions"
MAX_QUANTITY = 99


def get_cart(session):
    stored = session.get(CART_SESSION_KEY, {})
    if not isinstance(stored, dict):
        return {}
    generation = catalog_services.catalog_generation()
    if stored and session.get(CART_VERSION_KEY, "legacy") != generation:
        session[CART_SESSION_KEY] = {}
        session[CART_VERSION_KEY] = generation
        session[CART_NOTICE_KEY] = True
        session.modified = True
        return {}
    catalog = {str(p["id"]): p for p in catalog_services.get_products()}
    versions = session.get(CART_OFFERS_KEY, {})
    if not isinstance(versions, dict):
        versions = {}
    valid = {str(key): min(value, MAX_QUANTITY) for key, value in stored.items()
             if str(key) in catalog and type(value) is int and value > 0
             and (not catalog[str(key)].get("oferta_revisao")
                  or versions.get(str(key)) == catalog[str(key)]["oferta_revisao"])}
    if valid != stored:
        session[CART_SESSION_KEY] = valid
        session[CART_NOTICE_KEY] = True
        session.modified = True
    return valid


def cart_count(session):
    return sum(get_cart(session).values())


def set_quantity(session, product_id, quantity):
    if type(quantity) is not int or not 0 <= quantity <= MAX_QUANTITY:
        raise ValueError("Quantidade deve estar entre 0 e 99.")
    product = catalog_services.get_product(product_id)
    if not product:
        raise ValueError("Produto nao encontrado.")
    cart = get_cart(session).copy()
    key = str(product_id)
    if quantity:
        cart[key] = quantity
    else:
        cart.pop(key, None)
    session[CART_SESSION_KEY] = cart
    session[CART_VERSION_KEY] = catalog_services.catalog_generation()
    versions = session.get(CART_OFFERS_KEY, {})
    versions = versions.copy() if isinstance(versions, dict) else {}
    if quantity and product.get("oferta_revisao"):
        versions[key] = product["oferta_revisao"]
    else:
        versions.pop(key, None)
    session[CART_OFFERS_KEY] = {key: value for key, value in versions.items() if key in cart}
    session.modified = True


def add_to_cart(session, product_id):
    current = get_cart(session).get(str(product_id), 0)
    if current >= MAX_QUANTITY:
        raise ValueError("Limite de 99 unidades por modelo.")
    set_quantity(session, product_id, current + 1)


def remove_from_cart(session, product_id):
    set_quantity(session, product_id, max(0, get_cart(session).get(str(product_id), 0) - 1))


def get_cart_items(session):
    catalog = {str(p["id"]): p for p in catalog_services.get_products()}
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
