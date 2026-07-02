# TODOS

Working notes for what's next. Order matters: **make it work → verify → then make it swappable.**

## 1. Verify end-to-end persistence — ✅ DONE

Verified: first POST inserts (`times_seen = 1`); re-POST of same fixture bumps to `times_seen = 2` with no duplicate row. Both branches of the upsert proven. (Also fixed a latent bug: `IncidentORM` was missing a `service` column — added it.)

This is the green regression baseline for the refactor in #3.

## 2. Harden the upsert against the concurrent-duplicate race — ✅ DONE

`record_incident` is now a single atomic `INSERT ... ON CONFLICT (fingerprint) DO UPDATE` — no read-then-write, no race. `times_seen` increments in SQL (`IncidentORM.times_seen + 1`); changed fields refreshed via `stmt.excluded.*`; `progress_status` derived in Python from `incident.status`; `first_seen` left untouched on conflict. The old `get_incident_by_fingerprint` is now unused — keep it for `IncidentRepo.get_by_fingerprint` in #3.

## 3. Repository seam — swappable storage, vendor-neutral

Goal: not tied to a vendor. Same pattern as guitar_rag's LLM/embedding provider factory.

**The rule:** neutrality lives at the *interface*, not in every line.
- Interface = vendor-neutral: speaks the domain (`Incident`), never storage (`IncidentORM`, Mongo docs). No `session`/ORM objects in signatures.
- Implementation = vendor-*maximal*: `PostgresIncidentRepo` is allowed to be fully Postgres (uses `ON CONFLICT`). Each backend uses its own best atomic upsert (MySQL `ON DUPLICATE KEY UPDATE`, Mongo `update_one(..., upsert=True)`).

Steps:
1. Define `IncidentRepo` protocol (`typing.Protocol`), domain-typed:
   - `async def record(self, incident: Incident) -> None`
   - `async def get_by_fingerprint(self, fingerprint: str) -> Incident | None` (maps ORM row → domain `Incident` before returning)
2. Move current `db_service` logic into `PostgresIncidentRepo` implementing it.
3. Upgrade that impl's `record()` to the `ON CONFLICT` version from #2.
4. Factory `get_incident_repo()` reads `DB_BACKEND` env var, returns the right instance; point the endpoint at it.
5. Re-run the #1 test — still green = refactor preserved behavior.
6. Do NOT write `MongoIncidentRepo` until Mongo is actually wanted (build the seam, not speculative backends).

## Production-grade logging

Dev logging is in via `logging.basicConfig` + a module logger + `logger.exception`. Upgrade to production-grade later:

- Replace `basicConfig` with `logging.config.dictConfig` — centralized, explicit handlers/formatters/levels.
- Structured JSON logs (one dict per line) so they're machine-parseable by a log aggregator.
- Integrate with / override uvicorn's own log config so app logs and access logs share one format (uvicorn `--log-config`, or programmatic).
- Request correlation IDs (a per-request id threaded through log lines) so one webhook's logs can be traced end to end.
- Set levels via env/config (DEBUG in dev, INFO/WARNING in prod), not hardcoded.
- Make sure tracebacks still surface: keep `logger.exception` / bare `raise` in handlers; never flatten an error to a one-line `print`.

## Loose ends

- ~~Re-add `@cache` to `get_session_maker`.~~ Done (present in `db/database.py`).
- ~~Replace `print(...)` error handling in `app/main.py` with real logging.~~ Done (dev-grade; see Production-grade logging above for the upgrade).
