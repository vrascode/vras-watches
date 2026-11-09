"""Read the existing JSON catalog; keep its location and numeric contract."""
import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings


PRODUCTS_PATH = settings.BASE_DIR / "data" / "products.json"


def load_products(*, decimal_prices: bool = False) -> list[dict]:
    """Return fresh records; monetary calculations request Decimal decoding."""
    with Path(PRODUCTS_PATH).open(encoding="utf-8") as source:
        return json.load(source, parse_float=Decimal if decimal_prices else float)
