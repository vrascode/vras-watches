"""Only explicitly approved, local media may be published by the storefront."""
import json
import re
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
    if kind == "image":
        candidates = {}
        renditions = entry.get("renditions", [])
        for rendition in renditions if isinstance(renditions, list) else []:
            asset = local_asset(rendition)
            if asset and type(asset.get("width")) is int and asset["width"] > 0:
                candidates[asset["width"]] = asset["url"]
        if type(entry.get("width")) is int and entry["width"] > 0:
            candidates[entry["width"]] = result["url"]
        result["srcset"] = ", ".join(f"{url} {width}w" for width, url in sorted(candidates.items()))
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
    return {"image": local_asset(data.get("image")), "video": local_asset(data.get("video"), "video"),
            "mobile_image": local_asset(data.get("mobile_image"))}


def valid_instagram_permalink(url):
    if not isinstance(url, str):
        return False
    try:
        origin = urlsplit(url)
        return (origin.scheme == "https" and origin.hostname in {"instagram.com", "www.instagram.com"}
                and not origin.username and not origin.password
                and bool(re.fullmatch(r"/(?:p|reel|tv)/[A-Za-z0-9_-]+/?", origin.path)))
    except ValueError:
        return False


def instagram_posts(manifest):
    posts = []
    for entry in manifest.get("instagram", []):
        if not valid_instagram_permalink(entry.get("permalink")):
            continue
        image = local_asset(entry.get("image"))
        video = local_asset(entry.get("video"), "video")
        if image or video:
            posts.append({**entry, "image": image or video["poster"], "video": video})
    return posts
