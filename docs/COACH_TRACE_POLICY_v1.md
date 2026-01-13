# Coach Trace Policy v1

## Default: No Traces

By default, sg-curriculum does **not** store:
- Raw LLM prompts
- Raw LLM completions/responses
- Intermediate reasoning chains

Only **structured coach feedback** (conforming to `coach_feedback_v1.schema.json`) is persisted.

## Rationale

1. **Privacy**: Prompts may contain sensitive learner context
2. **Storage**: Raw traces are large and grow unboundedly
3. **Reproducibility**: Structured outputs are sufficient for debugging

## Opt-in Tracing (Future)

If trace storage is enabled in a future version:
- Traces will be stored locally only
- Traces will have explicit TTL (default: 7 days)
- Traces will be excluded from any export bundles

## Policy Version

This policy applies to coach_feedback_v1 and may be revised in v2.
