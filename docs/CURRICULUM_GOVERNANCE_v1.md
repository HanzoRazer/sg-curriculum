# Curriculum Governance v1

## Scope
This document governs all curriculum content and coaching policies within sg-curriculum.

## Principles

1. **Local-first**: All learner data stays on-device by default. No cloud accounts required in v1.
2. **Device-local identity**: Learners are identified by `device_learner_id`, not email/accounts.
3. **Structured outputs**: Coach feedback is machine-readable JSON, not free-form text.
4. **No prompt traces**: By default, LLM prompts/completions are NOT stored (see COACH_TRACE_POLICY).

## Contract Versioning

- All contracts use semantic versioning embedded in filename: `*_v1.schema.json`
- Once `CONTRACTS_VERSION.json` has `"public_released": true`, v1 schemas are **immutable**
- Breaking changes require a new version (v2) with migration tooling

## Change Process

1. Edit schema in `contracts/`
2. Regenerate `.sha256` file
3. Update `contracts/CHANGELOG.md` mentioning the schema stem
4. CI gates enforce all three requirements
