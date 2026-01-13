from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class RuntimeConfig:
    data_dir: Path
    db_path: Path
    device_secret_path: Path

    @staticmethod
    def load() -> "RuntimeConfig":
        # Local-first default: ./data
        base = Path(os.environ.get("SGC_DATA_DIR", "data")).resolve()
        base.mkdir(parents=True, exist_ok=True)
        db_path = base / "sgc.sqlite3"
        secret_path = base / "device_secret.bin"
        return RuntimeConfig(
            data_dir=base,
            db_path=db_path,
            device_secret_path=secret_path,
        )
