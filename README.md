# incident_triage

A FastAPI service that receives **Alertmanager webhooks**, normalizes each alert into an
`Incident`, deduplicates and prioritizes it, and persists it in Postgres — then serves the
open incidents back as a **priority-ranked worklist**.

---

## What it does

Alertmanager POSTs a batch of alerts to this service. The service:

1. Validates the webhook body against a Pydantic model (`Payload`).
2. Normalizes each alert into a domain `Incident` (severity, service, title, fingerprint).
3. Assigns a triage **priority** (P1–P4) from the alert's severity and the service's tier.
4. Persists and deduplicates on `fingerprint` in Postgres (repeat alerts bump `times_seen` / `last_seen`).
5. Returns `202 Accepted`.

Operators then read **`GET /incidents`** to get the open incidents back **ranked by priority** —
a triaged worklist instead of raw alert noise.

---

## Architecture

```
Alertmanager ── POST /webhooks/alertmanager/──▶ FastAPI (app/main.py)
                                                    │
                                       Payload.to_incidents()  (models/providers/alert_manager.py)
                                                    │
                                          domain Incident (models/incident.py, Pydantic)
                                                    │
                                          persist as Incident row
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

## Prioritization

Each incident gets a `Priority` (P1–P4) from a small, explicit rules **matrix** keyed on
`(severity, service tier)`. Service tiers are a config
lookup (`SERVICE_TIER`, default tier 3), so the matrix stays about *severity × how critical the
service is*. `GET /incidents` returns the open incidents ordered **P1 → P4** (freshest first
within a priority).

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

Then POST an Alertmanager-shaped payload (see `tests/fixtures/`) to `http://localhost:8000/webhooks/alertmanager/`,
and read the ranked worklist from `GET http://localhost:8000/incidents`.
Interactive docs at `http://localhost:8000/docs`.

## Test

```bash
uv run pytest
```

Fixtures in `tests/fixtures/` mirror real Alertmanager webhook bodies (single + multi-alert).

---

### Module dependency direction

`tables.py` (pure schema) ← `database.py` (engine/session) ← `db_service.py` (behavior). Each layer imports only *downward*, which is what keeps `Base.metadata` populated before `create_all` runs without a circular import.
