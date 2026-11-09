"""Offline import of owner-mapped, authorized originals. Never fetches URLs."""
import copy
import hashlib
import re
from pathlib import Path

from loja.media import assets as media
from loja.media.processing import optimize_image


def input_file(root, filename):
    if not isinstance(filename, str) or not filename or "\\" in filename or ":" in filename:
        raise ValueError("Informe um caminho relativo de arquivo local na pasta de entrada.")
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Arquivo ausente ou fora da pasta de entrada: {filename}")
    return path


def prepare_import(root, description, manifest, catalog):
    """Validate the complete batch and prepare outputs before touching the store."""
    root = Path(root).resolve()
    result = copy.deepcopy(manifest)
    outputs, imported, skipped = {}, [], []
    products = {str(p["id"]): p for p in catalog}
    seen = set()
    entries = description.get("assets")
    if not isinstance(entries, list):
        raise ValueError("O manifesto de entrada precisa conter uma lista assets.")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Cada entrada de assets precisa ser um objeto.")
        if entry.get("autorizado") is not True:
            skipped.append(entry.get("id", "sem ID"))
            continue
        identity = entry.get("id", "")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", identity) or identity in seen:
            raise ValueError("Cada mídia aprovada precisa de um ID único, com letras minúsculas, números e hífen.")
        seen.add(identity)
        if not all(isinstance(entry.get(key), str) and entry[key].strip() for key in ("origem", "comprovante", "alt")):
            raise ValueError(f"{identity}: informe origem, comprovante da autorização e texto alternativo.")
        destination = entry.get("destino")
        if destination not in {"product", "hero", "hero_mobile", "editorial", "campaign", "instagram"}:
            raise ValueError(f"{identity}: destino desconhecido.")
        product_id = str(entry.get("produto_id", ""))
        if destination == "product" and (product_id not in products or entry.get("produto_confirmado") is not True):
            raise ValueError(f"{identity}: confirme a associação exata com um ID de produto existente.")
        if destination == "product" and products[product_id].get("catalog_generation") == "poedagar-v1":
            source_variant = entry.get("variante_fonte_id")
            if type(source_variant) is not int or not any(v["source_sku_id"] == source_variant for v in products[product_id].get("variantes_fonte", [])):
                raise ValueError(f"{identity}: informe variante_fonte_id correspondente à fotografia e registrada no catálogo.")
        if destination == "instagram" and not media.valid_instagram_permalink(entry.get("permalink")):
            raise ValueError(f"{identity}: informe o permalink real da publicação original.")
        original = input_file(root, entry.get("arquivo"))
        slug = products.get(product_id, {}).get("slug", product_id)
        if destination == "product" and not re.fullmatch(r"[a-z0-9-]+", str(slug)):
            raise ValueError(f"{identity}: slug inválido no catálogo.")
        prefix = (f"img/products/poedagar/{slug}/{identity}" if destination == "product"
                  else f"img/brand/{identity}")
        provenance = f"{entry['origem']} | Autorização: {entry['comprovante']} | SHA256 original: {hashlib.sha256(original.read_bytes()).hexdigest()}"
        kind = entry.get("tipo", "image")
        if kind == "image":
            if original.suffix.lower() not in media.IMAGE_EXTENSIONS:
                raise ValueError(f"{identity}: formato de imagem não suportado.")
            asset = optimize_image(original, prefix, provenance, entry["alt"], outputs)
        elif kind == "video":
            if destination == "hero_mobile" or original.suffix.lower() not in media.VIDEO_EXTENSIONS:
                raise ValueError(f"{identity}: vídeo deve ser MP4/WebM; hero_mobile recebe fotografia.")
            if entry.get("video_otimizado") is not True:
                raise ValueError(f"{identity}: fornecer MP4 H.264/WebM otimizado para web e confirmar video_otimizado.")
            poster_path = input_file(root, entry.get("poster"))
            if poster_path.suffix.lower() not in media.IMAGE_EXTENSIONS:
                raise ValueError(f"{identity}: poster deve ser uma fotografia autorizada.")
            poster = optimize_image(poster_path, prefix + "-poster", provenance, entry["alt"], outputs)
            content = original.read_bytes()
            digest = hashlib.sha256(content).hexdigest()[:16]
            src = f"videos/imported/{identity}-{digest}{original.suffix.lower()}"
            outputs[src] = content
            asset = {"src": src, "poster": poster, "autorizado": True, "origem": provenance, "alt": entry["alt"]}
            if entry.get("legendas"):
                captions = input_file(root, entry["legendas"])
                if captions.suffix.lower() != ".vtt" or not captions.read_text(encoding="utf-8-sig").startswith("WEBVTT"):
                    raise ValueError(f"{identity}: legendas precisam estar em WebVTT.")
                caption_content = captions.read_bytes()
                caption_hash = hashlib.sha256(caption_content).hexdigest()[:16]
                caption_src = f"videos/imported/{identity}-{caption_hash}.vtt"
                outputs[caption_src] = caption_content
                asset["captions"] = {"src": caption_src, "autorizado": True, "origem": provenance}
        else:
            raise ValueError(f"{identity}: tipo deve ser image ou video.")
        asset["import_id"] = identity
        if destination == "product":
            asset["produto_id"] = int(product_id)
            asset["catalog_generation"] = products[product_id].get("catalog_generation", "legacy")
            asset["modelo"] = products[product_id].get("modelo")
            asset["source_variant_id"] = entry.get("variante_fonte_id")
            if kind == "video":
                for field in ("produto_id", "catalog_generation", "modelo", "source_variant_id"):
                    asset["poster"][field] = asset[field]
            group = result.setdefault("products", {}).setdefault(product_id, {})
            field = "images" if kind == "image" else "videos"
            collection = group.setdefault(field, [])
            previous = next((i for i, item in enumerate(collection) if item.get("import_id") == identity), None)
            if previous is None:
                collection.append(asset)
            else:
                collection[previous] = asset
        elif destination == "instagram":
            post = {"import_id": identity, "permalink": entry["permalink"], kind: asset}
            collection = result.setdefault("instagram", [])
            previous = next((i for i, item in enumerate(collection) if item.get("import_id") == identity), None)
            if previous is None:
                collection.append(post)
            else:
                collection[previous] = post
        else:
            section = "hero" if destination == "hero_mobile" else destination
            field = "mobile_image" if destination == "hero_mobile" else kind
            result.setdefault(section, {})[field] = asset
        imported.append(identity)
    return result, outputs, {"imported": imported, "skipped": skipped, "files": len(outputs)}
