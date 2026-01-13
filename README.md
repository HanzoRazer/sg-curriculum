# sg-curriculum (Local-first)

Canonical home for Smart Guitar curriculum + coaching + learner/session state.

## Owns
- Curriculum objects (lessons, drills, plans)
- Learner identity + sessions (device-local IDs; no accounts in v1)
- Performance summaries + attachment references
- Coaching outputs (structured) + trace policy

## Does NOT own
- CAM / toolpaths / G-code / RMOS authority or artifacts
- ToolBox contract definitions (only consumes ToolBox safe export bundles)
