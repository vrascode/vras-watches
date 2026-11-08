"""Read public unit prices and payment conditions; never applies selling prices."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


def amount(value):
    price = Decimal(str(value))
    if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
        raise ValueError("Preço ausente, não positivo ou com mais de dois decimais")
    return format(price, ".2f")


def inspect(product):
    url = product["fontes"]["url_modelo_e_preco"]
    result = {"product_id": product["id"], "model": product["modelo"], "url": url,
              "checked_at_utc": datetime.now(timezone.utc).isoformat(), "verified": False}
    try:
        origin = urlsplit(url)
        if origin.scheme != "https" or origin.hostname != "lojaspoedagar.com.br" or not origin.path.endswith("/p"):
            raise ValueError("URL não corresponde à fonte autorizada")
        with urlopen(Request(url, headers={"User-Agent": "VRAS-PriceVerification/1.0"}), timeout=30) as response:
            if urlsplit(response.url).hostname != origin.hostname:
                raise ValueError("Redirecionamento para outra fonte")
            raw = response.read()
        result["html_sha256"] = hashlib.sha256(raw).hexdigest()
        html = raw.decode("utf-8")
        start = re.search(r"window\.data\s*=\s*", html)
        if not start:
            raise ValueError("Dados públicos do produto não encontrados")
        remote = json.JSONDecoder().raw_decode(html[start.end():])[0]["product"]["data"]
        if remote["name"] != "Relógio " + product["nome"]:
            raise ValueError("O nome comercial não corresponde ao modelo VRAS")
        result.update(source_name=remote["name"], source_product_id=remote["id"], variants=[])
        expected = {v["source_sku_id"]: v for v in product["variantes_fonte"]}
        received = set()
        for sku in remote["skus"]["data"]:
            if sku["id"] not in expected or sku["title"] != expected[sku["id"]]["title"]:
                raise ValueError("Variante/ID da fonte mudou; requer conferência antes da aplicação")
            if sku["product_id"] != remote["id"] or sku["id"] in received:
                raise ValueError("Variante duplicada ou pertencente a outro modelo")
            received.add(sku["id"])
            price = sku["prices"]["data"]
            unit = amount(price["price"])
            billet = price.get("billet", {})
            # The advertised price is distinct from the lower Pix price and the
            # source's struck-through price. Do not infer a quantity/coupon offer.
            if (price.get("currency") != "R$" or amount(price["price_discount"]) != unit
                    or amount(billet.get("price")) != unit or billet.get("discount_percent") != 0):
                raise ValueError("Não foi possível distinguir preço unitário de condição de pagamento")
            result["variants"].append({
                "source_variant_id": sku["id"], "source_sku": sku["sku"], "title": sku["title"],
                "options": sku["variations"], "unit_price_brl": unit,
                "pix_price_brl": amount(price["pix"]["price"]) if price.get("pix") else None,
                "pix_discount_percent": price.get("pix", {}).get("discount_percent"),
                "billet_price_brl": amount(billet["price"]), "billet_discount_percent": billet["discount_percent"],
                "source_price_before_promotion_brl": amount(price["price_sale"]),
                "source_has_promotion": price["has_promotion"],
                "source_stock_status": sku["stock_status"], "source_blocked_sale": sku["blocked_sale"],
                "price_kind": "advertised_unit_price", "verified": True,
            })
        if not received or received != set(expected):
            raise ValueError("Nem todas as variantes cadastradas tiveram preço atual confirmado")
        result["verified"] = True
        result["condition_review"] = {
            "method": "HTML público window.data.product.data.skus.data[].prices.data",
            "selected_field": "price", "pix_used": False, "previous_price_used": False,
            "coupon_or_minimum_quantity_used": False,
            "observation": "Preço unitário do SKU coincide com boleto sem desconto adicional. Pix é separado. Não foi inserido cupom nem selecionada quantidade. A promoção própria da fonte não é criada na VRAS.",
            "installments_promised_by_vras": False,
        }
    except (ValueError, KeyError, TypeError, InvalidOperation, OSError) as error:
        result["error"] = str(error)
    return result


if __name__ == "__main__":
    catalog = json.loads((ROOT / "data/products.json").read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(inspect, catalog))
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "currency": "BRL",
              "scope": "12 modelos e suas variantes; somente consulta, sem aprovação automática", "products": results}
    (ROOT / "data/poedagar_price_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verified_models": sum(p["verified"] for p in results),
                      "verified_variants": sum(len(p.get("variants", [])) for p in results if p["verified"]),
                      "errors": [{"model": p["model"], "error": p.get("error")} for p in results if not p["verified"]]}, ensure_ascii=True))
