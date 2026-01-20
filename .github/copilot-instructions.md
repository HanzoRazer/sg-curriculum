# Copilot Instructions for sg-curriculum

## Domain Boundaries (CI-Enforced)

**Owns:** curriculum, coaching, device-local learner identity, performance summaries  
**Does NOT own:** CAM/toolpaths/G-code/RMOS—those belong to ToolBox repo

**Blocked terms** in `contracts/`: `gcode`, `toolpath`, `rmos`, `fixture`, `feedrate`, `spindle`, `cam`  
CI gate `scripts/ci/check_no_toolbox_terms.py` fails PRs using these terms.

## Quick Commands

```powershell
pip install -e ".[dev]"      # Install with dev deps
pytest -v                     # Run tests
sgc init                      # Initialize runtime (creates db + device identity)
sgc next --slot 1             # Generate assignment for learner slot
python scripts/ci/check_contracts_governance.py --repo-root .  # Validate contracts locally
```

## Architecture: Two Coach Implementations

| Location | Purpose | Data Model |
|----------|---------|------------|
| `runtime/policy.py` | CLI runtime coach (v0) | Dict-based, `pick_next_assignment()` + `coach_feedback_from_session()` |
| `src/sg_coach/coach_policy.py` | Full evaluation engine | Frozen dataclasses from `src/sg_coach/models.py` |

**Pattern**: Both use frozen `@dataclass` configs (`PolicyConfig`, `CoachPolicyConfig`) with explicit threshold knobs. Follow this when adding new policies.

**Domain types** in `src/sg_coach/models.py`: `SessionRecord`, `CoachEvaluation`, `ProgramRef`, `PerformanceSummary`. Use `model_copy(update={...})` for immutable updates.

## Contract Governance (CI-Enforced)

Every `.schema.json` in `contracts/` requires:
1. A `.schema.sha256` companion (64 lowercase hex, no newline)
2. An entry in `contracts/CHANGELOG.md` mentioning the schema stem name

**Regenerate hashes after schema edits:**
```powershell
cd contracts; Get-ChildItem *.schema.json | % { 
  $h = (Get-FileHash $_ -Algorithm SHA256).Hash.ToLower()
  Set-Content ($_.Name -replace '\.json$', '.sha256') $h -NoNewline
}
```

Once `contracts/CONTRACTS_VERSION.json` has `"public_released": true`, v1 schemas become **immutable**.

## Identity Model

- **No cloud accounts**—device-local only via `device_learner_id`
- Secret stored at `data/device_secret.bin`, ID derived via SHA256
- Multiple learners per device: `local_slot` 1-99 (see `runtime/identity.py`)
- ID format: `lrn_<base32hash>` for learners, `dev_<base32hash>` for devices

## SQLite Schema

`runtime/db.py` defines tables: `catalog`, `sessions`, `assignments`, `coach_feedback`, `attachments`. All JSON payloads stored as `*_json` TEXT columns. Use `PRAGMA journal_mode=WAL`.

## Groove Layer v0 (Accompaniment Adaptation)

The Groove Layer is **separate from coaching**—it drives *accompaniment adaptation*, not pedagogy.

**Signal path:** Event Extraction → **Groove Layer** (latent state + control intents) → Engine Host (BIAB etc.)

**Non-goals (v0):** pedagogy objects, player identity, raw audio/MIDI blobs, CAM/RMOS, cloud dependency.

### Implementation

Core module: `src/sg_groove/` with:
- `models.py` — `PerformanceEvent`, `EngineContext`, `WindowStats`, `GrooveState`, `GrooveLayerConfig`
- `window_eval.py` — `compute_window_stats()` for per-window evidence extraction
- `groove_layer.py` — `GrooveLayer` class + `process_fixture()` helper

### Inputs
- **Performance events:** `t_onset_ms`, `event_type`, `strength` (0–1), `confidence` (0–1)
- **Engine context:** `tempo_bpm_target`, `time_signature`, `grid`, `feel`, `bar_position`
- **System context:** `device_id`, `session_id`, `window_duration_ms` (default 15s)

### Outputs
- **Control output:** `groove_layer_control_v0` schema—emitted every window (~15s) and on major policy switches
- **Internal state:** fast state (session-only) + slow traits (cross-session)—NOT a public contract

### Latent Update Rule
```
latent ← (1 − α·w)·latent + (α·w)·evidence
```
- `α_fast = 0.20`, `α_med = 0.08`, `α_slow = 0.02`
- `w` = window confidence (0–1), gated by min 12 events/window

### Probing Rules
- Only probe when stability is above threshold
- Probe duration: 30–60s, frequency: ~every 6–10 min
- Must be reversible—revert if metrics worsen

### Degradation Behavior (fail boringly)
- Event stream degrades → drop `window.confidence`, freeze policies, `tempo.policy = steady_clock`
- Missing engine context → disable grid-based inferences, keep accompaniment steady
- Engine can't apply controls → treat as advisory, don't churn

### Latency Targets
- Event-to-control: ≤250ms median, ≤500ms p95
- Audio round-trip (if monitoring through stack): ≤10ms good, ≤15ms acceptable

## Key Extension Points

- **Assignment scoring**: Modify `pick_next_assignment()` in `runtime/policy.py`—drills prioritized over lessons
- **Feedback rubrics**: Add new `rubric_tags` in `coach_feedback_from_session()`
- **Thresholds**: Adjust frozen dataclass fields in `PolicyConfig` or `CoachPolicyConfig`
- **New findings**: Add `CoachFinding` entries in `evaluate_session()` with `Severity.primary|secondary|info`

## Testing Patterns

Tests in `tests/` use helper factories like `_base_session(**overrides)` to construct domain objects. Follow this pattern for new test fixtures. Run `pytest -v` before commits.

### Groove Layer v0 Fixtures

Deterministic test vectors in `fixtures/groove_v0/`:

| Vector | Scenario | Key Assertion |
|--------|----------|---------------|
| 01 | Stable timing | `tempo.policy = follow_player`, no loop |
| 02 | Unstable burst | Reduce density, micro-loop, disable probes |
| 03 | Recovery | De-escalate assist, restore density |
| 04 | Missing tempo | Freeze, no grid claims, no probes |
| 05 | Probe A/B | Probe only when stable, revert if hurts |

Event shape: `t_onset_ms`, `event_type`, `strength` (0–1), `confidence` (0–1)

