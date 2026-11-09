"""Apply an explicit owner approval to independently verified reference prices."""
import copy
from datetime import date
from decimal import Decimal, InvalidOperation


def money(value):
    try:
        amount = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Preço inválido") from error
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("Preço deve ser positivo, finito e ter até dois decimais")
    return amount.quantize(Decimal("0.01"))


def price_update(product, evidence, approval_record, approval_date):
    """No network, publication override, guessed variant, media or stock changes."""
    if not isinstance(approval_record, str) or not approval_record.strip():
        raise ValueError("É necessário registrar a autorização expressa do proprietário")
    date.fromisoformat(approval_date)
    expected_url = product["fontes"]["url_modelo_e_preco"]
    if (evidence.get("verified") is not True or evidence.get("error")
            or evidence.get("product_id") != product["id"] or evidence.get("model") != product["modelo"]
            or evidence.get("source_name") != "Relógio " + product["nome"] or evidence.get("url") != expected_url):
        raise ValueError("Consulta não confirmada ou pertencente a outro modelo")
    review = evidence.get("condition_review", {})
    if (review.get("selected_field") != "price" or review.get("pix_used") is not False
            or review.get("previous_price_used") is not False or review.get("coupon_or_minimum_quantity_used") is not False):
        raise ValueError("Não aplicar preço condicionado ou preço anterior")
    expected = {v["source_sku_id"]: v for v in product["variantes_fonte"]}
    variants = evidence.get("variants", [])
    if not variants or {v.get("source_variant_id") for v in variants} != set(expected) or len(variants) != len(expected):
        raise ValueError("A verificação não cobre exatamente as variantes deste modelo")
    approved = {}
    for variant in variants:
        source_id = variant["source_variant_id"]
        if (variant.get("verified") is not True or variant.get("price_kind") != "advertised_unit_price"
                or variant.get("title") != expected[source_id]["title"]):
            raise ValueError("Variante não corresponde ao preço verificado")
        unit = money(variant["unit_price_brl"])
        if money(variant["billet_price_brl"]) != unit or variant["billet_discount_percent"] != 0:
            raise ValueError("Preço unitário depende de condição não confirmada")
        approved[str(source_id)] = {
            "source_variant_id": source_id, "titulo_fonte": variant["title"], "valor": format(unit, ".2f"),
            "fonte": expected_url, "consulta_UTC": evidence["checked_at_utc"],
            "tipo_preco": "advertised_unit_price", "aprovado": True,
            "disponibilidade_na_fonte": variant["source_stock_status"],
        }
    amounts = {entry["valor"] for entry in approved.values()}
    if len(amounts) != 1:
        raise ValueError("Variantes têm preços distintos: confirmar a variante antes de definir o preço do modelo")
    value = next(iter(amounts))
    result = copy.deepcopy(product)
    result["preco"] = float(Decimal(value))  # JSON numeric value; runtime reads Decimal.
    result["aprovacao_preco"] = {
        "aprovado": True, "valor": value, "data": approval_date, "registro": approval_record.strip(),
        "source_variant_id": (product.get("variante") or {}).get("source_variant_id"),
        "fonte": expected_url, "consulta_UTC": evidence["checked_at_utc"],
        "escopo": "variantes_verificadas_com_preco_unitario_identico", "variantes": approved,
        "condicao": review["observation"],
    }
    result["fontes"]["preco_consultado_UTC"] = evidence["checked_at_utc"]
    result["pendencias"] = [entry for entry in result.get("pendencias", []) if "aprovação de preço" not in entry.casefold()]
    return result


def variant_approval_matches(product, approval, price):
    """Validate approval for the selected SKU, or uniform coverage while unselected."""
    selected_id = (product.get("variante") or {}).get("source_variant_id")
    entries = approval.get("variantes")
    if entries is None:  # Existing explicit approval for one selected SKU.
        return type(selected_id) is int and approval.get("source_variant_id") == selected_id
    if not isinstance(entries, dict) or not entries:
        return False
    observed = {str(v["source_sku_id"]): v for v in product.get("variantes_fonte", [])}

    def valid(key):
        entry = entries.get(key)
        if not isinstance(entry, dict) or key not in observed:
            return False
        try:
            return (entry.get("aprovado") is True and str(entry.get("source_variant_id")) == key
                    and entry.get("titulo_fonte") == observed[key].get("title")
                    and entry.get("fonte") == product.get("fontes", {}).get("url_modelo_e_preco")
                    and bool(entry.get("consulta_UTC")) and entry.get("tipo_preco") == "advertised_unit_price"
                    and money(entry.get("valor")) == price)
        except ValueError:
            return False

    if selected_id is not None:
        return type(selected_id) is int and valid(str(selected_id))
    # Approval can be complete before the physical SKU is confirmed, but that
    # never satisfies the independent identity/media/availability publication gates.
    return bool(observed) and set(entries) == set(observed) and all(valid(key) for key in observed)


def approved_price(product):
    approval = product.get("aprovacao_preco", {})
    if not isinstance(approval, dict) or approval.get("aprovado") is not True:
        return False
    try:
        price = Decimal(str(product.get("preco")))
        date.fromisoformat(approval.get("data", ""))
        return (price.is_finite() and price > 0 and price.as_tuple().exponent >= -2
                and price == Decimal(str(approval.get("valor")))
                and isinstance(approval.get("registro"), str) and bool(approval["registro"].strip())
                and variant_approval_matches(product, approval, price))
    except (ValueError, TypeError, InvalidOperation):
        return False
