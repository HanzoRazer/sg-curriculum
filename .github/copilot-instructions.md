# Copilot Instructions for sg-curriculum

## Domain Boundaries (CI-Enforced)

This repo owns: curriculum, coaching, device-local learner identity, performance summaries.
**Does NOT own**: CAM/toolpaths/G-code/RMOS—those belong to ToolBox repo.

**Blocked terms** in `contracts/`: `gcode`, `toolpath`, `rmos`, `fixture`, `feedrate`, `spindle`, `cam`  
CI gate `scripts/ci/check_no_toolbox_terms.py` will fail if these appear.

## Contract Governance (Must Follow)

Every `.schema.json` in `contracts/` requires:
1. A `.schema.sha256` companion (64 lowercase hex, no newline)
2. An entry in `contracts/CHANGELOG.md` mentioning the schema stem name

**Regenerate hashes (PowerShell):**
```powershell
cd contracts; Get-ChildItem *.schema.json | % { 
  $h = (Get-FileHash $_ -Algorithm SHA256).Hash.ToLower()
  Set-Content ($_.Name -replace '\.json$', '.sha256') $h -NoNewline
}
```

Once `contracts/CONTRACTS_VERSION.json` has `"public_released": true`, v1 schemas become **immutable**.

## Two Coach Implementations

| Location | Purpose | Use When |
|----------|---------|----------|
| `runtime/policy.py` | CLI runtime coach (v0) | `sgc` CLI commands |
| `src/sg_coach/coach_policy.py` | Full evaluation engine | Detailed session analysis with `SessionRecord` models |

Both use dataclass configs (`PolicyConfig`, `CoachPolicyConfig`) with explicit threshold knobs.

## Groove Layer (Musicianship Latent Vector)

The Groove Layer is a **separate concern** from coaching—it drives *accompaniment adaptation*, not pedagogy.

| Domain | Purpose | Example Dimensions |
|--------|---------|-------------------|
| Time & Groove | How player relates to time | `microtiming_bias`, `tempo_stability`, `swing_affinity` |
| Motor Consistency | Physical execution reliability | `attack_consistency`, `fatigue_resilience`, `error_recovery_speed` |
| Cognitive Load | Complexity absorption capacity | `complexity_tolerance`, `form_memory`, `adaptation_speed` |
| Interaction Preference | Musical preference (not skill) | `leader_follower_bias`, `repetition_preference`, `density_comfort` |

**Critical boundaries:**
- Latent values are **never shown** to users—they drive adaptation silently
- Outputs arrangement control signals (tempo policy, density, loop length)—**not** lessons or feedback
- Dimensions are `[0.0–1.0]` normalized with slow (trait) vs fast (state) update rates
- Does NOT include: skill levels, correctness scores, genre labels, achievements

**Update mechanics (v0):**
- Generic rule: `latent ← (1 − α·w)·latent + (α·w)·evidence`
- Learning rates: `α_fast=0.20` (state), `α_med=0.08`, `α_slow=0.02` (trait)
- Eligibility gating: skip update if <12 onsets, confidence <0.5, or unknown grid

**Probing policy:** Every ~8 min, probe preferences (leader/follower, density, repetition) for 30-60s when stability is above threshold—prevents bias lock-in.

**Output contract (arranger-facing):**
```json
{
  "tempo_policy": "follow_player | steady_clock | gentle_nudge",
  "density_target": "sparse | medium | full",
  "loop_policy": "none | 2bars | 4bars | 8bars",
  "change_policy": "avoid_modulation | allow_modulation"
}
```

## Identity Model

- **No cloud accounts**—device-local only via `device_learner_id`
- Secret at `data/device_secret.bin`, ID derived via SHA256
- Multiple learners per device: `local_slot` 1-99 (see `runtime/identity.py`)

## Quick Commands

```powershell
pip install -e ".[dev]"      # Install with dev deps
pytest -v                     # Run tests
sgc init                      # Initialize runtime (creates db + device identity)
sgc next --slot 1             # Generate assignment for learner slot
python scripts/ci/check_contracts_governance.py --repo-root .  # Validate contracts locally
```

## Key Extension Points

- **Assignment scoring**: `pick_next_assignment()` in `runtime/policy.py`—modify ranking logic
- **Feedback rubrics**: `coach_feedback_from_session()` for new `rubric_tags`
- **Thresholds**: Adjust `PolicyConfig` or `CoachPolicyConfig` dataclass fields

