# Copilot Instructions for sg-curriculum

## Project Overview

Local-first Smart Guitar curriculum + coaching + learner/session state. This repo owns curriculum objects, device-local learner identity, performance summaries, and structured coaching outputs.

**Does NOT own**: CAM/toolpaths/G-code/RMOS artifacts—those belong to ToolBox (separate repo).

## Architecture

```
sg-curriculum/
├── contracts/           # JSON Schema spine contracts (immutable after public release)
│   ├── *_v1.schema.json # Schema definitions
│   ├── *_v1.schema.sha256 # Hash companions (CI-enforced)
│   └── CONTRACTS_VERSION.json # Release gate flag
├── runtime/             # Local-first Python runtime
│   ├── config.py        # RuntimeConfig (data_dir, db_path, secret_path)
│   ├── identity.py      # Device-local identity (no accounts)
│   ├── db.py            # SQLite schema + migrations
│   ├── store.py         # CRUD helpers for catalog/sessions/assignments
│   ├── attachments.py   # Content-hash blob store
│   ├── policy.py        # Rule-based coach v0 (pick_next_assignment, coach_feedback)
│   ├── engine.py        # Glue: init_runtime, compute_assignment, ingest_session
│   └── cli.py           # CLI entry point (sgc command)
├── docs/                # Governance + policy docs
├── scripts/ci/          # CI gate scripts (Python)
├── tests/               # pytest test suite
└── .github/workflows/   # GitHub Actions CI
```

## Critical Patterns

### Contract Governance (Scenario-B gates)
- Every `.schema.json` requires a companion `.schema.sha256` (64 lowercase hex)
- Schema changes **must** update `contracts/CHANGELOG.md` mentioning the stem
- Once `CONTRACTS_VERSION.json` has `"public_released": true`, v1 schemas are **immutable**
- See [check_contracts_governance.py](scripts/ci/check_contracts_governance.py)

### Domain Boundary Enforcement
- **Blocked terms** in contracts/: `gcode`, `toolpath`, `rmos`, `fixture`, `feedrate`, `spindle`, `cam`
- CI gate [check_no_toolbox_terms.py](scripts/ci/check_no_toolbox_terms.py) enforces separation from ToolBox domain

### Identity Model (v1)
- Device-local IDs only (`device_learner_id`)—no cloud accounts
- Secret stored at `data/device_secret.bin`, ID derived via SHA256
- Multiple learners per device via `local_slot` (1-99)

### Data Storage
- SQLite database at `data/sgc.sqlite3` (WAL mode)
- Content-addressed attachments at `data/attachments/<sha256>.<ext>`
- All data stays on-device (local-first)

## Contracts Quick Reference

| Schema | Purpose |
|--------|---------|
| `attachments_manifest_v1` | References large artifacts by hash/URI (no blobs) |
| `curriculum_catalog_v1` | Lessons/drills metadata catalog |
| `assignment_v1` | Practice assignments from coach policy |
| `session_record_v1` | Local session with performance summaries |
| `coach_feedback_v1` | Structured coaching output (no prompt traces) |

## Development Workflow

```powershell
# Install package (editable + dev deps)
pip install -e ".[dev]"

# Run tests
pytest -v

# Initialize local runtime
sgc init

# Generate next assignment
sgc next --slot 1

# Ingest a session (stdin)
echo '{"attempts":[...]}' | sgc ingest-session
```

### Regenerate SHA256 hashes (PowerShell)
```powershell
cd contracts
Get-ChildItem *.schema.json | % { 
  $h = (Get-FileHash $_ -Algorithm SHA256).Hash.ToLower()
  Set-Content ($_.Name -replace '\.json$', '.sha256') $h -NoNewline
}
```

### Run CI gates locally
```powershell
python scripts/ci/check_contracts_governance.py --repo-root .
python scripts/ci/check_no_toolbox_terms.py --repo-root .
```

## Adding/Modifying Contracts

1. Edit/create schema in `contracts/`
2. Regenerate `.sha256` companion
3. Update `contracts/CHANGELOG.md` with schema stem name
4. CI will block if any step is missing

## Runtime Extension Points

- **Policy tuning**: Modify `PolicyConfig` in [runtime/policy.py](runtime/policy.py)
- **Coach logic**: Extend `coach_feedback_from_session()` for new rubric tags
- **Assignment strategy**: Customize `pick_next_assignment()` scoring

