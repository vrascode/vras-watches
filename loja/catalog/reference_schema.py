"""Validate retailer observations without inventing manufacturer references."""
from decimal import Decimal
from datetime import datetime
from urllib.parse import urlsplit

from loja.catalog.pricing import money


def source_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname != "poedagareco.com" or parsed.port
            or parsed.username or parsed.password or not parsed.path.startswith("/products/")):
        raise ValueError("Informe uma página pública de produto em poedagareco.com.")
    return value


def validate_observation(item):
    if not isinstance(item, dict):
        raise ValueError("Produto de referência deve ser um objeto.")
    for key in ("model", "name", "url", "checked_at", "description"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValueError(f"Campo obrigatório: {key}.")
    source_url(item["url"])
    datetime.fromisoformat(item["checked_at"])
    if not isinstance(item.get("specifications", {}), dict) or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in item.get("specifications", {}).items()):
        raise ValueError("Especificações devem mapear nomes para textos verificados.")
    if item.get("brand") != "Poedagar":
        raise ValueError("A marca original deve ser Poedagar.")
    money(item["price_brl"])
    variants = item.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("O modelo precisa ter variantes verificadas.")
    if any(not isinstance(v, dict) or not isinstance(v.get("title"), str) for v in variants):
        raise ValueError("Cada variante precisa ter um título textual.")
    titles = [v.get("title", "").strip() for v in variants]
    if any(not title for title in titles) or len(set(t.casefold() for t in titles)) != len(titles):
        raise ValueError("Variantes vazias ou duplicadas.")
    for variant in variants:
        amount = money(variant.get("price_brl", item["price_brl"]))
        if amount > Decimal("1000000"):
            raise ValueError("Preço fora do limite de importação.")
        if variant.get("source_id") is not None and type(variant["source_id"]) is not int:
            raise ValueError("ID da plataforma deve ser inteiro.")
    return item
