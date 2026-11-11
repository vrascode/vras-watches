"""Create responsive WebP files in memory, preserving proportions and color."""
import hashlib
from io import BytesIO

from PIL import Image, ImageCms, ImageOps


def optimize_image(path, prefix, provenance, alt, outputs, *, widths=(480, 800, 1200, 1920)):
    """Keep proportions, orientation, transparency and color; never crop/upscale."""
    with Image.open(path) as original:
        if getattr(original, "n_frames", 1) != 1:
            raise ValueError(f"Imagem animada exige revisão manual: {path.name}")
        photo = ImageOps.exif_transpose(original)
        profile = original.info.get("icc_profile")
        if profile:
            srgb = ImageCms.createProfile("sRGB")
            photo = ImageCms.profileToProfile(photo, BytesIO(profile), srgb,
                                             outputMode="RGBA" if "A" in photo.getbands() else "RGB")
            profile = ImageCms.ImageCmsProfile(srgb).tobytes()
        elif photo.mode == "CMYK":
            raise ValueError(f"Imagem CMYK sem perfil de cor: fornecer original RGB: {path.name}")
        else:
            photo = photo.convert("RGBA" if "A" in photo.getbands() or "transparency" in photo.info else "RGB")
        photo.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        renditions = []
        for width in sorted({min(size, photo.width) for size in widths}):
            resized = photo.resize((width, max(1, round(photo.height * width / photo.width))), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            resized.save(buffer, format="WEBP", quality=88, method=6, icc_profile=profile or b"")
            content = buffer.getvalue()
            digest = hashlib.sha256(content).hexdigest()[:16]
            src = f"{prefix}-{digest}-{width}.webp"
            outputs[src] = content
            renditions.append({"src": src, "width": width, "height": resized.height,
                               "autorizado": True, "origem": provenance, "alt": alt})
    return {**renditions[-1], "renditions": renditions[:-1]}
