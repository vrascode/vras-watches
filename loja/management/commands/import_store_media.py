import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from loja import media, services
from loja.media_import import prepare_import


class Command(BaseCommand):
    help = "Validate/import authorized local originals from midias-instagram; dry-run by default."

    def add_arguments(self, parser):
        parser.add_argument("--source", default=str(settings.BASE_DIR / "midias-instagram"))
        parser.add_argument("--apply", action="store_true", help="Save optimized assets and merge the media manifest")

    def handle(self, *args, **options):
        source = Path(options["source"]).resolve()
        description = source / "manifest.json"
        if not description.is_file():
            self.stdout.write("Nenhum manifest.json encontrado; nenhuma mídia ou preço alterado.")
            return
        try:
            plan = json.loads(description.read_text(encoding="utf-8-sig"))
            catalog = json.loads(Path(services.PRODUCTS_PATH).read_text(encoding="utf-8"))
            manifest, outputs, summary = prepare_import(source, plan, media.load_media(), catalog)
        except (ValueError, OSError, KeyError) as error:
            raise CommandError(f"Importação não aplicada: {error}") from error
        if options["apply"] and summary["imported"]:
            for src, content in outputs.items():
                path = settings.BASE_DIR / "static" / src
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.write_bytes(content)
                elif path.read_bytes() != content:
                    raise CommandError(f"Conflito de arquivo; manifesto preservado: {src}")
            target = Path(media.MEDIA_PATH)
            temporary = target.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(target)
        mode = "APLICADO" if options["apply"] else "SIMULAÇÃO"
        self.stdout.write(f"{mode}: {len(summary['imported'])} mídias, {summary['files']} arquivos otimizados; "
                          f"{len(summary['skipped'])} entradas sem autorização ignoradas. Preços preservados.")
