"""Private owner submissions, offline image import and normal gated publication."""
import copy
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from django.conf import settings

from loja.catalog import repository, services
from loja.catalog.publication import publish_ready_products
from loja.media import assets as media
from loja.media.import_service import prepare_import


ISSUE_LABELS = {
    "produto_em_rascunho": "Rascunho",
    "referencia_do_fabricante_nao_confirmada": "Referência do fabricante",
    "variante_nao_confirmada": "Variante real",
    "fotografia_autorizada_do_sku_pendente": "Foto autorizada correspondente",
    "oferta_vras_nao_confirmada": "Disponibilidade VRAS",
    "preco_sem_aprovacao_correspondente": "Preço aprovado para a variante",
    "galeria_com_midia_de_outro_sku_ou_variante": "Galeria contém outra variante; substituir as fotos",
    "identidade_diverge_do_modelo_cadastrado": "Identidade divergente",
    "variante_sem_correspondencia_na_fonte": "Variante sem correspondência",
    "poster_de_outro_sku_ou_variante": "Poster de outra variante",
}


def catalog_version():
    return hashlib.sha256(Path(repository.PRODUCTS_PATH).read_bytes() + b"\0" + Path(media.MEDIA_PATH).read_bytes()).hexdigest()


def atomic_bytes(target, content):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".receipt-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(target)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def receive_product(product_id, data, *, actor):
    """Accept only form-validated human attestations; never infer them from photos."""
    target, manifest_path = Path(repository.PRODUCTS_PATH), Path(media.MEDIA_PATH)
    lock = target.parent / ".owner-intake.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError("Outro recebimento está em andamento. Aguarde e atualize a página.") from error
    os.close(descriptor)
    try:
        original, original_media = target.read_bytes(), manifest_path.read_bytes()
        version = hashlib.sha256(original + b"\0" + original_media).hexdigest()
        if data["catalog_version"] != version:
            raise ValueError("O catálogo mudou. Atualize a página antes de enviar novamente.")
        catalog, manifest = json.loads(original), json.loads(original_media)
        product = next((p for p in catalog if p["id"] == product_id), None)
        if not product or product.get("catalog_generation") != "poedagar-v1":
            raise ValueError("Produto Poedagar não encontrado.")
        variant_id = data.get("variante")
        if variant_id is not None and not any(v["source_sku_id"] == variant_id for v in product["variantes_fonte"]):
            raise ValueError("Variante não pertence a este modelo.")
        submitted_at = datetime.now(timezone.utc).isoformat()
        receipt_id = uuid4().hex
        root = settings.BASE_DIR / "midias-instagram" / "recebidos" / receipt_id
        root.mkdir(parents=True)
        # Immutable before-images and originals stay private, outside static/.
        (root / "before-products.json").write_bytes(original)
        (root / "before-media.json").write_bytes(original_media)
        _apply_attestations(product, data, actor=actor, submitted_at=submitted_at, receipt_id=receipt_id)
        if data.get("acao_galeria") == "replace":
            manifest.setdefault("products", {})[str(product_id)] = {"images": [], "videos": []}
            for name in ("galeria", "videos"):
                product[name] = []
            product.pop("capa", None)
        entries = _store_originals(root, product, data, receipt_id)
        plan = {"assets": entries}
        (root / "manifest.json").write_bytes(json_bytes(plan))
        updated_media, outputs, summary = prepare_import(root, plan, manifest, catalog)
        if data.get("usar_banner"):
            new_ids = set(summary["imported"])
            image = next(a for a in updated_media["products"][str(product_id)]["images"] if a["import_id"] in new_ids)
            updated_media["hero"] = {"image": copy.deepcopy(image), "video": None, "mobile_image": None}
        receipt = {"id": receipt_id, "product_id": product_id, "actor": actor, "submitted_at_utc": submitted_at,
                   "fields": {key: value for key, value in data.items() if key not in {"fotos", "catalog_version"}},
                   "imported": summary["imported"], "status": "validated"}
        (root / "receipt.json").write_bytes(json_bytes(receipt))
        for src, content in outputs.items():
            path = settings.BASE_DIR / "static" / src
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != content:
                raise ValueError("Conflito de arquivo derivado; catálogo preservado.")
            if not path.exists():
                path.write_bytes(content)
        if target.read_bytes() != original or manifest_path.read_bytes() != original_media:
            raise ValueError("Catálogo ou mídias mudaram durante o envio; dados recebidos foram preservados para revisão.")
        # A draft is committed first: interruption can never expose a half-updated offer.
        atomic_bytes(target, json_bytes(catalog))
        atomic_bytes(manifest_path, json_bytes(updated_media))
        result = publish_ready_products(apply=True)
        receipt.update(status="applied", publication=result)
        (root / "receipt.json").write_bytes(json_bytes(receipt))
        return {"receipt": receipt_id, "imported": len(summary["imported"]), "publication": result}
    finally:
        lock.unlink(missing_ok=True)


def owner_products():
    products = services.get_products(include_drafts=True)
    for product in products:
        product["pending_labels"] = [ISSUE_LABELS.get(issue, issue) for issue in product["publication_issues"]
                                     if issue != "produto_em_rascunho"]
    return products


def _apply_attestations(product: dict, data: dict, *, actor: str, submitted_at: str, receipt_id: str) -> None:
    """Record explicit confirmations and revise the offer when its binding changes."""
    previous = copy.deepcopy(product)
    variant_id = data.get("variante")
    product["status"] = "rascunho"
    product["referencia"] = data.get("referencia") or None
    product["identificacao"] = {
        "confirmada": data["identidade_confirmada"], "marca": product["marca"], "modelo": product["modelo"],
        "referencia": data.get("referencia", ""), "fonte": data.get("fonte", ""),
        "conferido_por": actor, "conferido_em_UTC": submitted_at,
    }
    product["variante"] = {
        "confirmada": data["variante_confirmada"], "source_variant_id": variant_id,
        "cor": f"Caixa {data.get('cor_caixa', '')}; mostrador {data.get('cor_mostrador', '')}",
        "pulseira": f"{data.get('tipo_pulseira', '')} — {data.get('cor_pulseira', '')}",
        **{key: data.get(key, "") for key in ("cor_caixa", "cor_mostrador", "cor_pulseira", "tipo_pulseira")},
        "fonte": data.get("fonte", ""), "conferido_por": actor, "conferido_em_UTC": submitted_at,
    }
    product["oferta_confirmada"] = data["oferta_confirmada"]
    binding_changed = (previous.get("referencia") != product["referencia"] or
                       (previous.get("variante") or {}).get("source_variant_id") != variant_id)
    product["oferta_revisao"] = (receipt_id if binding_changed else previous.get("oferta_revisao") or receipt_id)
    product["confirmacao_oferta"] = {
        "registro": data.get("registro_oferta", ""), "conferido_por": actor, "conferido_em_UTC": submitted_at,
    }
    if binding_changed:
        product["especificacoes"] = {}


def _store_originals(root: Path, product: dict, data: dict, receipt_id: str) -> list[dict]:
    """Keep originals private and prepare the existing authorized import contract."""
    product_id = product["id"]
    variant_id = data.get("variante")
    entries = []
    for index, upload in enumerate(data.get("fotos", []), 1):
        suffix = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "AVIF": ".avif"}[upload.image.format]
        filename = f"original-{index}{suffix}"
        with (root / filename).open("wb") as output:
            for chunk in upload.chunks():
                output.write(chunk)
        entries.append({
            "id": f"owner-{product_id}-{receipt_id}-{index}", "arquivo": filename, "tipo": "image",
            "destino": "product", "produto_id": product_id, "variante_fonte_id": variant_id,
            "produto_confirmado": data["variante_confirmada"], "autorizado": data["fotos_autorizadas"],
            "origem": data["origem"], "comprovante": data["comprovante"],
            "alt": f"Poedagar {product['modelo']} — {product['variante']['cor']}; {product['variante']['pulseira']} — foto {index}",
        })
    return entries
