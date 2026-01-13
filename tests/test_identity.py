from pathlib import Path
from runtime.identity import ensure_device_identity, device_learner_id


def test_device_identity_stable(tmp_path: Path):
    secret = tmp_path / "secret.bin"
    d1 = ensure_device_identity(secret)
    d2 = ensure_device_identity(secret)
    assert d1.device_id == d2.device_id
    assert d1.device_secret_sha256 == d2.device_secret_sha256

    l1 = device_learner_id(d1, 1)
    l2 = device_learner_id(d1, 1)
    assert l1 == l2
