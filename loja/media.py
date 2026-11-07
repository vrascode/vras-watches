"""Only explicitly approved, local media may be published by the storefront."""
import json
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from django.conf import settings
from django.templatetags.static import static

MEDIA_PATH = settings.BASE_DIR / "data" / "media.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}


def local_asset(entry, kind="image"):
    if not isinstance(entry, dict) or entry.get("autorizado") is not True or not entry.get("origem"):
        return None
    src = entry.get("src", "")
    if not isinstance(src, str) or "\\" in src or ":" in src:
        return None
    path = PurePosixPath(src)
    root = (settings.BASE_DIR / "static").resolve()
    target = (root / src).resolve()
    extensions = VIDEO_EXTENSIONS if kind == "video" else {".vtt"} if kind == "caption" else IMAGE_EXTENSIONS
    if (path.is_absolute() or ".." in path.parts or not target.is_relative_to(root)
            or path.suffix.lower() not in extensions or not target.is_file()):
        return None
    result = {**entry, "src": src, "url": static(src), "kind": kind}
    if kind == "video":
        poster = local_asset(entry.get("poster"))
        if not poster:
            return None
        result["poster"] = poster
        result["mime"] = "video/webm" if path.suffix.lower() == ".webm" else "video/mp4"
        result["captions"] = local_asset(entry.get("captions"), "caption")
    return result


def load_media():
    with Path(MEDIA_PATH).open(encoding="utf-8") as source:
        return json.load(source)


def approved_paths():
    approved = set()

    def visit(value):
        if isinstance(value, dict):
            if "src" in value:
                suffix = Path(value.get("src", "")).suffix.lower()
                kind = "video" if suffix in VIDEO_EXTENSIONS else "caption" if suffix == ".vtt" else "image"
                asset = local_asset(value, kind)
                if asset:
                    approved.add(asset["src"])
            for entry in value.values():
                visit(entry)
        elif isinstance(value, list):
            for entry in value:
                visit(entry)

    visit(load_media())
    # Optional inline product galleries use the same approval contract as the manifest.
    with (settings.BASE_DIR / "data/products.json").open(encoding="utf-8") as source:
        visit(json.load(source))
    return approved


def section_media(manifest, section):
    data = manifest.get(section, {})
    return {"image": local_asset(data.get("image")), "video": local_asset(data.get("video"), "video")}


def instagram_posts(manifest):
    posts = []
    for entry in manifest.get("instagram", []):
        origin = urlsplit(entry.get("permalink", ""))
        if (origin.scheme != "https" or origin.hostname not in {"instagram.com", "www.instagram.com"}
                or not origin.path.startswith(("/p/", "/reel/", "/tv/"))):
            continue
        image = local_asset(entry.get("image"))
        video = local_asset(entry.get("video"), "video")
        if image or video:
            posts.append({**entry, "image": image or video["poster"], "video": video})
    return posts
