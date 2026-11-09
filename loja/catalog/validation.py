"""Identity, variant and publication gates shared by every entry point."""
from urllib.parse import urlsplit

from loja.catalog.pricing import approved_price
from loja.utils import normalize


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


def publication_issues(product):
    """A researched listing is not an approved offer from VRAS."""
    issues = []
    if product.get("catalog_generation") == "poedagar-v1" and product["id"] in range(1, 13):
        issues.append("id_aposentado_nao_pode_ser_reutilizado")
    if product.get("status") != "publicado":
        issues.append("produto_em_rascunho")
    if not approved_price(product):
        issues.append("preco_sem_aprovacao_correspondente")
    identity = product.get("verified_identity")
    if not identity:
        issues.append("referencia_do_fabricante_nao_confirmada")
    elif any(normalize(str(product.get(key, ""))) != normalize(identity[key]) for key in ("marca", "modelo", "referencia")):
        issues.append("identidade_diverge_do_modelo_cadastrado")
    variant = product.get("verified_variant")
    if not variant:
        issues.append("variante_nao_confirmada")
    elif not any(v.get("source_sku_id") == variant.get("source_variant_id")
                 for v in product.get("variantes_fonte", [])):
        issues.append("variante_sem_correspondencia_na_fonte")
    cover = product.get("cover")
    def corresponding(asset):
        return (asset and asset.get("produto_id") == product["id"]
                and asset.get("catalog_generation") == product.get("catalog_generation")
                and asset.get("modelo") == product.get("modelo")
                and asset.get("source_variant_id") == (variant or {}).get("source_variant_id"))
    if not corresponding(cover):
        issues.append("fotografia_autorizada_do_sku_pendente")
    if any(not corresponding(asset) for asset in product.get("images", []) + product.get("videos", [])):
        issues.append("galeria_com_midia_de_outro_sku_ou_variante")
    if any(not corresponding(video.get("poster")) for video in product.get("videos", [])):
        issues.append("poster_de_outro_sku_ou_variante")
    if product.get("oferta_confirmada") is not True:
        issues.append("oferta_vras_nao_confirmada")
    return issues
