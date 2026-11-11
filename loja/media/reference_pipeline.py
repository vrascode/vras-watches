"""Preserve public originals, inspect files and create responsive local renditions."""
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from PIL import Image

from django.conf import settings
from django.utils.text import slugify

from loja.catalog.reference_storage import atomic_write
from loja.media.processing import optimize_image
from loja.media.download_diagnostics import describe_failure
from loja.media.public_download import download
from loja.media.reference_inventory import relative_original_path


def video_resolution(path):
    executable = shutil.which("ffprobe")
    if not executable:
        return None
    process = subprocess.run([executable, "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height", "-of", "json", str(path)],
                             capture_output=True, text=True, timeout=30, check=True)
    stream = json.loads(process.stdout).get("streams", [])
    return {key: stream[0][key] for key in ("width", "height")} if stream else None


def import_inventory(items, *, root=None, fetch=download):
    root = Path(root or settings.BASE_DIR).resolve()
    result = copy.deepcopy(items)
    for item in result:
        stage = "download"
        try:
            relative = relative_original_path(item)
            path = root.joinpath(*relative.parts).resolve()
            if not path.is_relative_to(root / "media-originals"):
                raise ValueError("Destino fora do projeto.")
            if path.is_file() and item.get("sha256"):
                content = path.read_bytes()
                if hashlib.sha256(content).hexdigest() != item["sha256"]:
                    raise ValueError("Hash do original preservado diverge do inventário.")
            else:
                content, mime = fetch(item["original_url"])
                if not mime.startswith(("image/", "video/")):
                    raise ValueError("A resposta não contém imagem ou vídeo.")
                if path.exists() and path.read_bytes() != content:
                    raise ValueError("A origem mudou; o original preservado não será sobrescrito.")
                if not path.exists():
                    atomic_write(path, content)
            item.update(original_path=relative.as_posix(), sha256=hashlib.sha256(content).hexdigest(),
                        download_status="downloaded", error=None, failure=None)
            stage = "processing"
            if item["type"] == "image":
                with Image.open(path) as original:
                    original.verify()
                with Image.open(path) as original:
                    item["resolution"] = {"width": original.width, "height": original.height}
                item["resolution_status"] = "file_verified"
                prefix = f"img/products/poedagar/{slugify(item['product'])}/{slugify(item.get('variant') or 'geral')}/{item['id']}"
                outputs = {}
                authorization = item["commercial_authorization"]
                provenance = f"{item['original_url']} | {authorization['record']} | Titularidade não verificada | SHA256 {item['sha256']}"
                asset = optimize_image(path, prefix, provenance, f"Poedagar {item['product']} / {item.get('variant') or 'geral'}", outputs,
                                       widths=(160, 480, 800, 1200, 1920))
                for filename, payload in outputs.items():
                    atomic_write(root / "static" / filename, payload)
                item["optimized_paths"] = list(outputs)
                item["asset"] = asset
            elif item["type"] == "video":
                resolution = video_resolution(path)
                if resolution:
                    item["resolution"], item["resolution_status"] = resolution, "file_verified"
                item["video_processing_status"] = "original_preserved"
                from loja.media.video_processing import optimize_video
                outputs = {}
                prefix = f"videos/poedagar/{slugify(item['product'])}/{slugify(item.get('variant') or 'geral')}/{item['id']}"
                authorization = item["commercial_authorization"]
                provenance = f"{item['original_url']} | {authorization['record']} | SHA256 {item['sha256']}"
                item["asset"] = optimize_video(path, prefix, provenance, f"Poedagar {item['product']}", outputs)
                for filename, payload in outputs.items():
                    atomic_write(root / "static" / filename, payload)
                item["optimized_paths"] = list(outputs)
                item["video_processing_status"] = "silent_h264_with_poster"
            item["processing_status"] = "complete"
        except (OSError, ValueError, Image.DecompressionBombError, subprocess.SubprocessError) as error:
            if stage == "download":
                item["download_status"] = "error"
            item["processing_status"] = "error"
            item["failure"] = describe_failure(error, stage)
            item["last_attempt_at"] = datetime.now(timezone.utc).isoformat()
            item["error"] = str(error)[:1000]
    return result
