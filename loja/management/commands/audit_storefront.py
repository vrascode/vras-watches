import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja import media, services


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
            raw = json.loads(Path(services.PRODUCTS_PATH).read_text(encoding="utf-8"))
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
            for field in ("nome", "descricao", "categoria", "imagem"):
                if not isinstance(product.get(field), str) or not product[field].strip():
                    errors.append(f"Produto {product_id}: campo {field} invalido")
            try:
                price = Decimal(str(product.get("preco")))
                if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
                    errors.append(f"Produto {product_id}: preco invalido")
            except InvalidOperation:
                errors.append(f"Produto {product_id}: preco invalido")
            legacy = "img/products/" + product.get("imagem", "")
            associations[legacy].append(f"{product_id}: {product.get('nome', '')}")
            if not (settings.BASE_DIR / "static" / legacy).is_file():
                self.stderr.write(f"LEGADO AUSENTE (bloqueado): {legacy}")

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
            f"{len(approved)} arquivos aprovados, {len(manifest.get('instagram', []))} posts."
        ))
