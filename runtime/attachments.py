from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Tuple


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def put_blob(data_dir: Path, blob: bytes, ext: str) -> Tuple[str, Path]:
    """
    Stores blob under: data/attachments/<sha256>.<ext>
    Returns (sha256, path)
    """
    sha = sha256_bytes(blob)
    adir = data_dir / "attachments"
    adir.mkdir(parents=True, exist_ok=True)
    safe_ext = ext.lstrip(".") or "bin"
    path = adir / f"{sha}.{safe_ext}"
    if not path.exists():
        path.write_bytes(blob)
    return sha, path
