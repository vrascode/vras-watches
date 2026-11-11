"""Offline helper for download_poedagar_media.ps1. Never opens a network connection."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loja.media.local_reference import main


if __name__ == "__main__":
    raise SystemExit(main())
