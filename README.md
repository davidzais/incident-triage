# incident_triage

A FastAPI service that receives **Alertmanager webhooks**, normalizes each alert into an
`Incident`, and (eventually) persists/deduplicates them in Postgres for triage.

> Living document — update the **Status** and **Next steps** sections as the project moves.

---

## What it does

Alertmanager POSTs a batch of alerts to this service. The service:

1. Validates the webhook body against a Pydantic model (`Payload`).
2. Normalizes each alert into a domain `Incident` (severity, service, title, fingerprint).
3. Returns `202 Accepted` with the parsed incidents.

Persistence and deduplication (via `fingerprint`) are the next milestones.

---

## Architecture

```
Alertmanager ──POST /webhooks/alertmanager/──▶ FastAPI (app/main.py)
                                                    │
                                       Payload.to_incidents()  (models/providers/alert_manager.py)
                                                    │
                                          domain Incident (models/incident.py, Pydantic)
                                                    │
                                        [planned] persist as Incident row
                                                    │
                                          SQLAlchemy async ──▶ Postgres 17
                                            (db/database.py)
```

### Layout

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app + the `/webhooks/alertmanager/` endpoint |
| `models/incident.py` | Domain models & enums (`Incident`, `Severity`, `AlertState`) — single source of truth for domain enums |
| `models/providers/alert_manager.py` | Alertmanager webhook schema (`Payload`, `Alert`, …) + `to_incidents()` mapping |
| `db/tables.py` | ORM schema: `Base`, `IncidentORM` table, `Status` enum |
| `db/database.py` | Engine, session factory (`get_session_maker`), `init_db()` |
| `db/db_service.py` | Data-access layer — `record_incident()` (insert-or-dedupe on `fingerprint`) |
| `db/docker_compose.yaml` | Local Postgres 17 |
| `tests/` | pytest suite + Alertmanager JSON fixtures |

---

## Domain model notes

- **Enums live in `models/incident.py`** and are all `StrEnum` (the member *is* its string value).
- **Two status axes, kept separate on purpose:**
  - `AlertState` (`firing` / `resolved`) — what Alertmanager reports. A **closed contract**, so it's *strict*: an unexpected value should raise, not be swallowed.
  - `Status` (`OPEN` / `CLOSED`) — the human triage lifecycle.
- `Severity` comes from a free-form label, so it's **lenient**: `from_raw()` normalizes and `_missing_` falls back to `UNKNOWN`.
- Rule of thumb: **open/untrusted input → lenient; closed/contract input → strict.**

---

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Run everything **from this directory** (`incident_triage/`) — it's the import root.

```bash
# install deps into .venv
uv sync

# start Postgres (reads POSTGRES_* from .env)
docker compose -f db/docker_compose.yaml up -d

# create tables
uv run python db/database.py
```

### Environment (`.env`)

| Var | Purpose |
|-----|---------|
| `DATABASE_URL` | SQLAlchemy async URL, e.g. `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Consumed by docker compose |

---

## Run

```bash
uv run uvicorn app.main:api --reload
```

Then POST an Alertmanager-shaped payload (see `tests/fixtures/`) to `http://localhost:8000/webhooks/alertmanager/`.
Interactive docs at `http://localhost:8000/docs`.

## Test

```bash
uv run pytest
```

Fixtures in `tests/fixtures/` mirror real Alertmanager webhook bodies (single + multi-alert).

---

## Status

- ✅ Webhook endpoint parses Alertmanager payloads and returns normalized incidents
- ✅ Domain enums (`Severity`, `Status`, `AlertState`) defined and typed
- ✅ `AlertState` validated at the boundary (`Alert.status: AlertState` → bad value = 422) and carried through to the domain `Incident`
- ✅ ORM schema (`IncidentORM`) split into `tables.py`; `Base` imported by `database.py`
- ✅ `init_db()` creates tables; session factory (`get_session_maker`) in place
- ✅ Persistence + dedupe in `db_service.record_incident()` — single atomic `INSERT ... ON CONFLICT` upsert; **verified end to end** (insert `times_seen=1`, re-POST bumps to `2`, no duplicate)
- ✅ Endpoint calls `record_incident()`; failures logged with traceback (`logger.exception`) and re-raised
- 🚧 Storage is Postgres-specific — repository seam (vendor-neutral interface) not built yet

## Next steps

1. **Repository seam** — extract storage behind a vendor-neutral `IncidentRepo` interface (`typing.Protocol`) with a `PostgresIncidentRepo` impl + factory, so backends (Mongo, etc.) can be swapped. See `TODOS.md`.
2. Add a DB-backed test for `record_incident` (insert path + dedupe/bump path) to lock in the verified behavior.
3. Production-grade logging (`dictConfig`, structured JSON, correlation IDs) — see `TODOS.md`.

### Module dependency direction

`tables.py` (pure schema) ← `database.py` (engine/session) ← `db_service.py` (behavior). Each layer imports only *downward*, which is what keeps `Base.metadata` populated before `create_all` runs without a circular import.
