# hermes-notes-api

A small, AI-assisted classroom demo for reviewing two independent pull requests: a validation bug fix and a keyword-filter enhancement. It is deliberately a local teaching application, not a deployed service.

## Requirements and commands

Python 3.10 or newer; only the Python standard library is used. No installation, credentials, database, or network service is required. Verified locally with Python 3.14.7.

From this repository directory:

```bash
python -B notes_api.py
python -B -m unittest discover -v
```

The server binds **only to `127.0.0.1`**. The default port is 8000; use `python -B notes_api.py --port 8001` if occupied, or `--port 0` to select an available loopback port. Stop with Ctrl+C. The command intentionally has no public-host option.

## API

| Method | Path | Success |
| --- | --- | --- |
| GET | `/notes` | `200 {"notes": [...]}` in creation order |
| POST | `/notes` | `201 {"id": 1, "text": "..."}` |
| DELETE | `/notes/<id>` | `204`, empty body |

IDs are increasing integers and are not reused within a server instance. JSON note objects use **`text`**, not `title`. Valid text is stored exactly as supplied, including surrounding whitespace. JSON object fields other than `text` are ignored.

Example commands for bash (on Windows, use `curl.exe` if your shell aliases `curl`):

```bash
curl -i http://127.0.0.1:8000/notes
curl -i -X POST http://127.0.0.1:8000/notes -H 'Content-Type: application/json' --data '{"text":"Prepare the demo"}'
curl -i http://127.0.0.1:8000/notes
curl -i -X DELETE http://127.0.0.1:8000/notes/1
```

POST requires `Content-Length` (curl sets it for `--data`) and JSON content type. Request bodies are limited to **16,384 bytes**. Malformed JSON, invalid UTF-8, missing/non-string text, and empty text return 400. Missing length returns 411, oversized bodies 413, and unsupported content types 415. Unknown routes and missing note IDs return 404. Errors have a JSON `error` field. Unsupported HTTP methods use the standard-library server's default response.

## State, safety, and the deliberate demo bug

- Notes live only in memory. Restarting the process loses all notes; separate handler factories have independent stores.
- No persistence, authentication, credentials, deployment, or production hardening is provided. Even on loopback, local programs can access it. Do not use real private notes.
- **Intentional limitation:** whitespace-only text such as `" \t\n "` is accepted. The baseline rejects `""` but does not strip whitespace for validation. This is the seeded bug-fix presentation scenario, not an accidental claim of correct validation.
- The bug-fix contract is to reject whitespace-only text with 400 without mutating the store, while preserving nonblank text exactly; do not silently trim stored text.
- Keyword query filtering is **not implemented**. Query parameters currently leave the list unfiltered. The enhancement scenario proposes `GET /notes?q=keyword`.

The baseline suite exercises real HTTP on ephemeral loopback ports and shuts down each test server. The deliberately failing presentation tests are kept outside this repository, in the sibling `scenarios/hermes-notes-api/` directory, so default discovery stays green. That directory includes the two scenario descriptions, copy-ready tests, exact acceptance commands, isolated replay copies, and local verification logs. Treat the scenarios as independent PRs from this baseline.

## AI-assisted development disclosure

This demo's source, tests, documentation, and scenario seeds were generated with AI assistance and exercised locally with standard-library tests. Review the code and test evidence before using it for instruction. No chat transcripts, private prompts, tokens, or credentials belong in this repository.
