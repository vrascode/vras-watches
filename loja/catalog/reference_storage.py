"""Atomic JSON writes, optimistic concurrency and a shared owner/import lock."""
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_write(path, content, *, expected=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".import-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        if expected is not None and path.read_bytes() != expected:
            raise ValueError("Arquivo alterado durante a importação; execute novamente.")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def catalog_lock():
    path = settings.BASE_DIR / "data/.owner-intake.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise ValueError("Há outra operação de catálogo em andamento.") from error
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)
