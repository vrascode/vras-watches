"""Safely publish complete offers without changing prices or confirmations."""
import json
import os
import tempfile
from pathlib import Path

from loja.catalog import repository, services, validation
from loja.media import assets as media


class PublicationError(ValueError):
    """The catalog cannot be safely published in its current state."""


def publish_ready_products(*, apply: bool = False) -> dict:
    """Dry-run by default; recheck files before an atomic publication write."""
    target = Path(repository.PRODUCTS_PATH)
    media_path = Path(media.MEDIA_PATH)
    try:
        original = target.read_bytes()
        original_media = media_path.read_bytes()
        catalog = json.loads(original)
        if not isinstance(catalog, list):
            raise ValueError("O catálogo deve ser uma lista")
        ids = [p["id"] for p in catalog]
        if (any(type(value) is not int or value <= 0 for value in ids)
                or len(ids) != len(set(ids))):
            raise ValueError("IDs inválidos ou duplicados")
        if any(p.get("status") not in {"rascunho", "publicado"} for p in catalog):
            raise ValueError("Status deve ser rascunho ou publicado")
        products = services.get_products(include_drafts=True)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise PublicationError(f"Publicação não aplicada: {error}") from error

    def check_unchanged():
        if target.read_bytes() != original or media_path.read_bytes() != original_media:
            raise PublicationError("Catálogo ou mídias mudaram durante a validação; execute novamente.")

    check_unchanged()
    ready, blocked, already_published = [], [], []
    for product in products:
        # Evaluate the prospective state with the exact storefront validator.
        # No identity, stock, variant or media confirmation is supplied here.
        candidate = {**product, "status": "publicado"}
        issues = validation.publication_issues(candidate)
        if issues:
            blocked.append({"id": product["id"], "modelo": product["modelo"],
                            "status": product["status"], "issues": issues})
        elif product["status"] == "rascunho":
            ready.append(product["id"])
        else:
            already_published.append(product["id"])

    if apply and ready:
        for product in catalog:
            if product["id"] in ready:
                product["status"] = "publicado"
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                             dir=target.parent, prefix=".publish-", suffix=".tmp",
                                             delete=False) as output:
                temporary = Path(output.name)
                json.dump(catalog, output, ensure_ascii=False, indent=2)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            check_unchanged()
            temporary.replace(target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    return {
        "apply_requested": apply,
        "changed": bool(apply and ready),
        "ready_products": ready,
        "published_products": ready if apply else [],
        "already_published": already_published,
        "blocked_products": blocked,
    }
