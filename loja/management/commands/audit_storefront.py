import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja.catalog import repository, services, validation
from loja.media import assets as media


def manifest_assets(value, destination="manifest"):
    if isinstance(value, dict):
        if "src" in value:
            yield destination, value
        for key, entry in value.items():
            yield from manifest_assets(entry, f"{destination}.{key}")
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            yield from manifest_assets(entry, f"{destination}[{index}]")


class Command(BaseCommand):
    help = "Validate catalog/media and optionally export the local asset provenance inventory."

    def add_arguments(self, parser):
        parser.add_argument("--write-inventory", action="store_true")

    def handle(self, *args, **options):
        try:
            raw = json.loads(Path(repository.PRODUCTS_PATH).read_text(encoding="utf-8"))
            manifest = media.load_media()
        except (OSError, ValueError) as error:
            raise CommandError(f"JSON invalido ou inacessivel: {error}") from error
        errors = []
        ids = set()
        associations = defaultdict(list)
        for product in raw:
            product_id = product.get("id")
            if type(product_id) is not int or product_id <= 0 or product_id in ids:
                errors.append(f"ID invalido ou duplicado: {product_id}")
            ids.add(product_id)
            for field in ("nome", "descricao", "categoria"):
                if not isinstance(product.get(field), str) or not product[field].strip():
                    errors.append(f"Produto {product_id}: campo {field} invalido")
            if product.get("status") not in {"rascunho", "publicado"}:
                errors.append(f"Produto {product_id}: status deve ser rascunho ou publicado")
            if product.get("preco") is not None or product.get("status") != "rascunho":
                try:
                    price = Decimal(str(product.get("preco")))
                    if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
                        errors.append(f"Produto {product_id}: preco invalido")
                except InvalidOperation:
                    errors.append(f"Produto {product_id}: preco invalido")
            if product.get("imagem"):
                legacy = "img/products/" + product["imagem"]
                associations[legacy].append(f"{product_id}: {product.get('nome', '')}")
                if not (settings.BASE_DIR / "static" / legacy).is_file():
                    self.stderr.write(f"LEGADO AUSENTE (bloqueado): {legacy}")
            identity = product.get("identificacao", {})
            identity_valid = validation.verified_record(identity, ("marca", "modelo", "referencia", "fonte"))
            if isinstance(identity, dict) and identity.get("confirmada") is True and not identity_valid:
                errors.append(f"Produto {product_id}: identificacao marcada confirmada sem referencia/fonte valida")
            variant = product.get("variante", {})
            if isinstance(variant, dict) and variant.get("confirmada") is True and (
                    not identity_valid or not validation.verified_record(variant, ("cor", "pulseira", "fonte"))):
                errors.append(f"Produto {product_id}: variante confirmada sem identidade/cor/pulseira/fonte valida")
            specs = product.get("especificacoes", {})
            if not isinstance(specs, dict):
                errors.append(f"Produto {product_id}: especificacoes devem ser um objeto")
            else:
                for label, entry in specs.items():
                    if isinstance(entry, dict) and entry.get("confirmada") is True and not validation.verified_record(entry, ("valor", "fonte")):
                        errors.append(f"Produto {product_id}: especificacao confirmada sem valor/fonte valida: {label}")

        if not errors:
            for product in services.get_products(include_drafts=True):
                if product.get("status") == "publicado" and product["publication_issues"]:
                    errors.append(f"Produto {product['id']}: publicação bloqueada: {', '.join(product['publication_issues'])}")
        approved = defaultdict(list)
        for destination, entry in manifest_assets({"manifest": manifest, "products": raw}):
            suffix = Path(entry.get("src", "")).suffix.lower()
            kind = "video" if suffix in media.VIDEO_EXTENSIONS else "caption" if suffix == ".vtt" else "image"
            if entry.get("autorizado") is True:
                if not media.local_asset(entry, kind):
                    errors.append(f"Midia aprovada invalida ou poster ausente: {destination}")
                approved[entry.get("src")].append((destination, entry.get("origem", "")))
        for product_id in manifest.get("products", {}):
            if not str(product_id).isdigit() or int(product_id) not in ids:
                errors.append(f"Midias associadas a produto inexistente: {product_id}")
        for post in manifest.get("instagram", []):
            if not media.instagram_posts({"instagram": [post]}):
                errors.append("Instagram: publicacao sem permalink oficial ou midia autorizada valida")
        root = settings.BASE_DIR / "static"
        files = sorted(path for path in root.rglob("*") if path.is_file()
                       and path.suffix.lower() in media.IMAGE_EXTENSIONS | media.VIDEO_EXTENSIONS | {".svg", ".mov", ".vtt"})
        if options["write_inventory"]:
            target = settings.BASE_DIR / "docs" / "MEDIA_INVENTORY.csv"
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("w", encoding="utf-8", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(["arquivo", "formato", "bytes", "sha256", "produto", "origem", "destino", "status"])
                for path in files:
                    src = path.relative_to(root).as_posix()
                    refs = approved.get(src, [])
                    writer.writerow([src, path.suffix[1:], path.stat().st_size,
                                     hashlib.sha256(path.read_bytes()).hexdigest(),
                                     "; ".join(associations.get(src, [])),
                                     "; ".join(ref[1] for ref in refs) or "Repositorio local preexistente; autoria nao confirmada",
                                     "; ".join(ref[0] for ref in refs) or "Preservado no arquivo; nao publicado",
                                     "aprovado" if refs else "bloqueado: procedencia pendente"])
            self.stdout.write(f"Inventario: {target.relative_to(settings.BASE_DIR)} ({len(files)} arquivos)")
        if errors:
            raise CommandError("\n".join(errors))
        self.stdout.write(self.style.SUCCESS(
            f"OK: {len(raw)} produtos, {len(ids)} IDs unicos, {len(files)} midias locais, "
            f"{len(approved)} arquivos aprovados, {len(manifest.get('instagram', []))} posts, "
            f"{sum(p.get('status') == 'rascunho' for p in raw)} rascunhos."
        ))
