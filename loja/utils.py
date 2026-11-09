"""Shared text normalization and BRL presentation."""
import unicodedata
from decimal import Decimal


def normalize(value):
    return "".join(char for char in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(char))


def format_brl(value):
    return f"R$ {Decimal(str(value)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
