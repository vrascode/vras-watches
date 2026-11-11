"""Idempotent additive imports; retailer names are commercial model evidence."""
import copy
import hashlib
import json
from datetime import date
from decimal import Decimal
from urllib.parse import unquote, urlsplit

from django.utils.text import slugify

from loja.catalog import repository
from loja.catalog.reference_schema import validate_observation
from loja.catalog.reference_storage import atomic_write, catalog_lock, encode


APPROVAL = "Solicitação expressa do proprietário em 2026-11-10: aplicar o preço unitário público da referência à VRAS Watches."


def variant_key(observation, variant):
    return observation["url"].split("?", 1)[0].rstrip("/") + "#" + variant["title"].strip().casefold()


def prepare_catalog(catalog, observations):
    result = copy.deepcopy(catalog)
    identities = [p["id"] for p in result]
    if len(identities) != len(set(identities)):
        raise ValueError("Catálogo existente contém IDs duplicados.")
    keys = [p["reference_key"] for p in result if p.get("reference_key")]
    if len(keys) != len(set(keys)):
        raise ValueError("Catálogo existente contém chaves de importação duplicadas.")
    indexed = {p["reference_key"]: p for p in result if p.get("reference_key")}
    next_id = max([24] + identities) + 1
    seen, created, updated = set(), [], []
    for observation in observations:
        validate_observation(observation)
        for variant in observation["variants"]:
            key = variant_key(observation, variant)
            if key in seen:
                raise ValueError("Modelo/variante duplicado no lote.")
            seen.add(key)
            product = indexed.get(key)
            if product is None:
                product = {"id": next_id, "status": "rascunho", "oferta_confirmada": False,
                           "galeria": [], "videos": [], "imagem": None, "variante": None,
                           "identificacao": {"confirmada": False}, "referencia": None}
                result.append(product)
                indexed[key] = product
                created.append(next_id)
                next_id += 1
            else:
                updated.append(product["id"])
            # Not a manufacturer/SKU number: page observations get a labeled surrogate.
            source_id = variant.get("source_id") or int(hashlib.sha256(key.encode()).hexdigest()[:12], 16)
            value = format(Decimal(str(variant.get("price_brl", observation["price_brl"]))), ".2f")
            old_price = product.get("preco")
            old_source = product.get("variantes_fonte", [{}])[0].get("source_sku_id") if product.get("variantes_fonte") else None
            product.update({
                "reference_key": key, "reference_import": True, "source_model_url": observation["url"],
                "source_id_kind": "platform_variant" if variant.get("source_id") else "derived_observation_id",
                "slug": slugify(observation["model"] + " " + variant["title"]),
                "nome": "Poedagar " + observation["model"] + " — " + variant["title"],
                "marca": "Poedagar", "modelo": observation["model"], "catalog_generation": "poedagar-v1",
                "preco": float(value), "categoria": "Poedagar", "destaque": observation["model"] == "Montelux",
                "descricao": observation["description"], "reference_color": variant["title"],
                "source_available": variant.get("available"),
                "fontes": {"url_modelo_e_preco": observation["url"], "consulta_UTC": observation["checked_at"],
                           "nome_comercial_verificado": True, "referencia_fabricante_verificada": False},
                "variantes_fonte": [{"source_sku_id": source_id, "title": variant["title"],
                                    "price_brl": float(value), "source_available": variant.get("available")}],
                "especificacoes": {label: {"valor": val, "fonte": observation["url"], "confirmada": True,
                                         "verification_scope": "retailer_statement"}
                                   for label, val in observation.get("specifications", {}).items()},
                "aprovacao_preco": {"aprovado": True, "valor": value, "data": date.today().isoformat(),
                                    "registro": APPROVAL, "source_variant_id": source_id,
                                    "fonte": observation["url"], "consulta_UTC": observation["checked_at"]},
                "pendencias": ["Confirmar referência e variante do produto fornecido", "Importar mídias correspondentes", "Confirmar atendimento da oferta VRAS"],
            })
            if old_source is not None and old_source != source_id:
                product["status"] = "rascunho"
                product["variante"] = None
            if old_price is not None and old_price != product["preco"]:
                product["oferta_revisao"] = hashlib.sha256(f"{key}:{value}".encode()).hexdigest()[:20]
            if product.get("variante") is None:
                product["variante"] = {"confirmada": False, "source_variant_id": source_id,
                                      "cor": variant["title"], "pulseira": "", "fonte": observation["url"]}
            product["source_handle"] = unquote(urlsplit(observation["url"]).path.rsplit("/", 1)[-1])
    return result, {"created": created, "updated": updated, "total": len(result)}


def import_observations(observations, *, apply=False):
    with catalog_lock():
        original = repository.PRODUCTS_PATH.read_bytes()
        result, report = prepare_catalog(json.loads(original), observations)
        report["applied"] = apply
        if apply:
            atomic_write(repository.PRODUCTS_PATH, encode(result), expected=original)
        return report
