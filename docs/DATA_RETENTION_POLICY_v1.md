# Data Retention Policy v1

## Scope
Defines retention rules for learner data within sg-curriculum local storage.

## Device-Local Data

| Data Type | Default Retention | Notes |
|-----------|-------------------|-------|
| Session records | Indefinite | Stored locally on device |
| Attachments (audio/MIDI) | 90 days | Content-addressed; prunable |
| Coach feedback | Indefinite | Structured JSON only |
| Assignments | Until superseded | Replaced on new generation |

## No Cloud Sync (v1)

- All data remains on the originating device
- No account-based sync or backup in v1
- Users may export data manually via safe export bundles

## Deletion

- Users can delete all local data at any time
- Deletion is permanent (no cloud backup exists)
