"""Export a full HTML catalog and one file per model with embedded local assets."""
import base64
import copy
import json
import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from loja.catalog.print_catalog import catalog_context
from loja.catalog.reference_storage import atomic_write


def embed_local_photos(context):
    context = copy.deepcopy(context)
    for section in context["catalog_sections"]:
        for product in section["variants"]:
            photo = product.get("cover")
            if not photo or photo.get("external") or not photo.get("src"):
                continue
            root = (settings.BASE_DIR / "static").resolve()
            path = (root / photo["src"]).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError("Fotografia local fora do diretório de estáticos.")
            mime = mimetypes.guess_type(path.name)[0] or "image/webp"
            photo["url"] = "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    return context


class Command(BaseCommand):
    help = "Exporta catálogo Poedagar completo e por modelo; fotos externas exigem internet."

    def add_arguments(self, parser):
        parser.add_argument("--output", default=str(settings.BASE_DIR / "artifacts/catalogos/poedagar"))

    def handle(self, *args, **options):
        try:
            output = Path(options["output"]).resolve()
            context = embed_local_photos(catalog_context())
            context.update(standalone=True,
                catalog_css=(settings.BASE_DIR / "static/css/poedagar-catalog.css").read_text(encoding="utf-8"),
                catalog_js=(settings.BASE_DIR / "static/js/poedagar-catalog.js").read_text(encoding="utf-8"))
            documents = [("index.html", context)]
            for section in context["catalog_sections"]:
                documents.append((section["slug"] + ".html", {
                    **context, "catalog_sections": [section], "catalog_model": section["name"],
                    "model_count": 1, "color_count": len(section["variants"]),
                }))
            for name, content in documents:
                atomic_write(output / name, render_to_string("loja/catalog/print_catalog.html", content).encode("utf-8"))
            external = sum(bool((p.get("cover") or {}).get("external")) for s in context["catalog_sections"] for p in s["variants"])
            self.stdout.write(json.dumps({"output": str(output), "files": len(documents),
                "models": context["model_count"], "colors": context["color_count"],
                "external_images": external}, ensure_ascii=True))
        except (OSError, ValueError) as error:
            raise CommandError(str(error)) from error
