"""Create a silent H.264 demonstration and a real poster; preserve the input."""
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from loja.media.processing import optimize_image


def optimize_video(original, prefix, provenance, alt, outputs):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg não está disponível; vídeo original preservado, processamento pendente.")
    with tempfile.TemporaryDirectory(prefix="vras-video-", dir=Path(original).parent) as temporary:
        target = Path(temporary) / "demonstration.mp4"
        poster = Path(temporary) / "poster.png"
        subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", str(original), "-an",
                        "-vf", "scale=w='min(1440,iw)':h=-2", "-c:v", "libx264", "-crf", "20",
                        "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        "-y", str(target)], check=True, capture_output=True, timeout=240)
        subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", str(target), "-frames:v", "1",
                        "-y", str(poster)], check=True, capture_output=True, timeout=30)
        content = target.read_bytes()
        digest = hashlib.sha256(content).hexdigest()[:16]
        src = f"{prefix}-{digest}.mp4"
        outputs[src] = content
        photo = optimize_image(poster, prefix + "-poster", provenance, alt, outputs)
        return {"src": src, "poster": photo, "autorizado": True, "origem": provenance, "alt": alt}
