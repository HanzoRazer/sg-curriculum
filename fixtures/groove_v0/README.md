# Groove Layer v0 Test Vectors

Deterministic test fixtures for validating Groove Layer behavior.

## Layout

```
vectors/     # Input event streams + engine context
expected/    # Expected control outputs per vector
acceptance/  # Machine-checkable assertions
```

## Conventions

- Times are **monotonic ms** starting at 0
- Window duration = **15000ms** (default)
- Event stream is onset-based (no raw audio)
- Engine context is either fixed or explicitly `null` (missing)

## Event Shape

Minimal event fields:
- `t_onset_ms` — monotonic timestamp in milliseconds
- `event_type` — `note_onset | strum_onset | percussive_onset`
- `strength` — 0.0–1.0 (envelope peak)
- `confidence` — 0.0–1.0 (detector confidence)

## Vectors

| Vector | Scenario | Key Assertion |
|--------|----------|---------------|
| 01 | Stable timing | `tempo.policy = follow_player`, no loop |
| 02 | Unstable burst | Reduce density, micro-loop, disable probes |
| 03 | Recovery | De-escalate assist, restore density |
| 04 | Missing tempo | Freeze, no grid claims, no probes |
| 05 | Probe A/B | Probe only when stable, revert if hurts |

## Running

```python
# Example harness outline
from pathlib import Path
import json

def load_vector(name: str):
    return json.loads((Path(__file__).parent / "vectors" / f"{name}.json").read_text())

def load_expected(name: str):
    return json.loads((Path(__file__).parent / "expected" / f"{name}.json").read_text())

def test_vector(name: str, groove_layer_fn):
    vector = load_vector(name)
    expected = load_expected(name)
    actual = groove_layer_fn(vector)
    # Compare actual vs expected controls
    ...
```
