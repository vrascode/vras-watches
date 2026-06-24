import json
from pathlib import Path

from django.conf import settings


PRODUCTS_PATH = settings.BASE_DIR / "data" / "products.json"
CART_SESSION_KEY = "cart"


def format_brl(value):
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _with_prices(product):
    product = product.copy()
    product["preco_brl"] = format_brl(product["preco"])
    return product


def get_products():
    with Path(PRODUCTS_PATH).open(encoding="utf-8") as products_file:
        return [_with_prices(product) for product in json.load(products_file)]


def get_featured_products():
    return [product for product in get_products() if product.get("destaque")]


def get_product(product_id):
    product_id = int(product_id)
    return next((product for product in get_products() if product["id"] == product_id), None)


def get_categories():
    return sorted({product["categoria"] for product in get_products()})


def filter_products(category=None, query=None):
    products = get_products()

    if category:
        products = [
            product for product in products
            if product["categoria"].lower() == category.lower()
        ]

    if query:
        search = query.lower()
        products = [
            product for product in products
            if search in product["nome"].lower()
            or search in product["descricao"].lower()
            or search in product["categoria"].lower()
        ]

    return products


def get_cart(session):
    return session.get(CART_SESSION_KEY, {})


def cart_count(session):
    return sum(get_cart(session).values())


def add_to_cart(session, product_id):
    cart = get_cart(session).copy()
    product_id = str(product_id)
    cart[product_id] = cart.get(product_id, 0) + 1
    session[CART_SESSION_KEY] = cart
    session.modified = True


def remove_from_cart(session, product_id):
    cart = get_cart(session).copy()
    product_id = str(product_id)

    if product_id in cart:
        if cart[product_id] > 1:
            cart[product_id] -= 1
        else:
            cart.pop(product_id)

    session[CART_SESSION_KEY] = cart
    session.modified = True


def get_cart_items(session):
    items = []

    for product_id, quantity in get_cart(session).items():
        product = get_product(product_id)
        if product:
            subtotal = product["preco"] * quantity
            items.append({
                "product": product,
                "quantity": quantity,
                "unit_price": product["preco"],
                "subtotal": subtotal,
                "subtotal_brl": format_brl(subtotal),
            })

    return items


def cart_total(session):
    return sum(item["subtotal"] for item in get_cart_items(session))


def cart_summary(session):
    items = get_cart_items(session)
    total = sum(item["subtotal"] for item in items)
    quantity = sum(item["quantity"] for item in items)

    return {
        "items": items,
        "quantity": quantity,
        "total": total,
        "total_brl": format_brl(total),
    }
