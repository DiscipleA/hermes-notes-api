# Filter GET /notes by an optional keyword query

AI-assisted demonstration planning artifact. No feature implementation is included.

## Acceptance criteria
- [ ] GET /notes?q=keyword performs URL-decoded, trimmed, case-insensitive substring matching.
- [ ] Absent or blank q returns all notes; preserve insertion order and stored text.
- [ ] No matches returns HTTP 200 with an empty list; filtering never mutates the store.

## Test plan
Add behavior tests first, observe failure, implement only the approved enhancement, and rerun the full baseline suite.

## Status
Draft planning only. Waiting for owner authorization; the maintenance job must leave this branch unchanged.
