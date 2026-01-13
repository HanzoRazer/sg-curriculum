from __future__ import annotations
import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    device_secret_sha256: str


def _b32(n: bytes) -> str:
    return base64.b32encode(n).decode("ascii").rstrip("=").lower()


def ensure_device_identity(secret_path: Path) -> DeviceIdentity:
    """
    Device-local identity:
    - secret stored on device
    - device_id derived from secret hash (non-reversible)
    """
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    if not secret_path.exists():
        secret_path.write_bytes(os.urandom(32))

    secret = secret_path.read_bytes()
    h = hashlib.sha256(secret).digest()
    device_id = "dev_" + _b32(h[:10])  # short stable ID
    secret_hex = hashlib.sha256(secret).hexdigest()
    return DeviceIdentity(device_id=device_id, device_secret_sha256=secret_hex)


def device_learner_id(device: DeviceIdentity, local_slot: int = 1) -> str:
    """
    Multiple local learners on one device: learner IDs are derived from device secret hash + slot.
    No names, no accounts.
    """
    if local_slot < 1 or local_slot > 99:
        raise ValueError("local_slot must be 1..99")
    material = f"{device.device_secret_sha256}:{local_slot}".encode("utf-8")
    h = hashlib.sha256(material).digest()
    return "lrn_" + _b32(h[:12])
