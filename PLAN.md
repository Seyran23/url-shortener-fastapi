# URL Shortener — Learning Roadmap (FastAPI + PostgreSQL + Redis + Telegram)

## Context

The user is new to Python (knows basic syntax) and wants to learn FastAPI by building a
production-oriented URL Shortener. The real goal is not the app — it's using the app as a
vehicle to learn Python-specific concepts: type hints, async/await, asyncio, decorators,
context managers, exceptions, concurrency, background processing, and clean architecture.

**Working mode (confirmed with user):** the user writes all the code themselves. Claude acts
as a guide/mentor only — explaining concepts, breaking each stage into concrete tasks,
pointing out gotchas, reviewing code the user pastes back, and correcting mistakes. **Claude
will not write or edit any project code unless the user explicitly asks for that at that
moment.** This plan itself is the only file Claude writes proactively.

**Confirmed tech decisions:**
- Async SQLAlchemy 2.0 from day one (`asyncpg` driver) — matches the async/await learning goal.
- Postgres (and later Redis) run via Docker Compose during development.
- Country-from-IP: local MaxMind GeoLite2 DB via `geoip2` (no network call in the redirect
  path). Device/browser/OS: `user-agents` package parsing the `User-Agent` header.
- Telegram bot: `aiogram` (async-native, fits the project's async theme) + `APScheduler` for
  daily/weekly report jobs.
- No API keys — auth is JWT-based (OAuth2 password flow), matching the original brief.

The project directory is currently empty — this is a from-scratch build, staged so each stage
produces something runnable before the next layer of complexity is added.

## How to use this roadmap

Each stage lists: **Concepts** (what to learn before/while doing it), **Build** (what to
implement), **Watch out for** (the specific gotcha this stage exists to teach), and **Done
when** (a concrete checkpoint). Work through stages in order — don't jump to analytics or the
Telegram bot before the core link CRUD + redirect is solid. When the user is ready for a
stage, ask Claude to explain the concepts and review code as they write it.

---

## Stage 0 — Environment & project skeleton
**Concepts:** virtual environments, `pip`/`venv` (or `uv`), project layout conventions.
**Build:** venv, install `fastapi`, `uvicorn[standard]`; a `docker-compose.yml` with a
Postgres service; base package layout (`app/api`, `app/core`, `app/models`, `app/schemas`,
`app/services`, `app/db`).
**Done when:** `docker compose up` starts Postgres, and a bare FastAPI app with one `/health`
route runs under `uvicorn --reload`.

## Stage 1 — FastAPI fundamentals
**Concepts:** type hints, Pydantic models (request/response schemas), path/query params,
FastAPI's dependency injection (`Depends`), automatic `/docs`.
**Build:** a couple of throwaway toy endpoints to get comfortable with request/response
models and `Depends` before touching the database.
**Done when:** the user can explain, in their own words, why FastAPI wants a Pydantic model
instead of a raw dict for request bodies.

## Stage 2 — Async database layer
**Concepts:** async/await mechanics, SQLAlchemy 2.0 async engine/session, the async session
as a context manager (`async with`), Alembic migrations, connection pooling basics.
**Build:** `User` and `Link` ORM models; async engine + `async_sessionmaker`; a
`get_db` dependency yielding a session (this is the first hands-on context-manager pattern);
Alembic wired up and first migration applied.
**Watch out for:** forgetting to `await` session calls, and session lifetime bugs (using a
session outside its `async with` block).
**Done when:** migrations create `users` and `links` tables in Postgres, verified with `psql`.

## Stage 3 — Auth (register/login)
**Concepts:** password hashing (`passlib`/`argon2`), JWT issuing/verification, OAuth2 password
flow (`OAuth2PasswordBearer`), custom exceptions vs `HTTPException`, decorators (route
decorators, and optionally a custom `@require_auth`-style dependency), Pydantic validators
(`EmailStr`, password rules).
**Build:** `POST /auth/register`, `POST /auth/login` (returns JWT), `GET /users/me`; a
`get_current_user` dependency.
**Done when:** a registered user can log in and hit `/users/me` with a Bearer token; wrong
password returns 401, not a 500.

## Stage 4 — Link CRUD + the custom-alias race condition
**Concepts:** DB unique constraints, catching `IntegrityError`, transactions
(commit/rollback), short-code generation (base62/random), URL validation
(`AnyHttpUrl`/custom validator), offset or keyset pagination.
**Build:** `POST /links` (auto-generated or custom alias, optional expiration date, optional
max-click limit), `GET /links` (paginated, scoped to the owner), `GET/PATCH/DELETE /links/{id}`,
enable/disable toggle.
**Watch out for:** the classic bug — checking "does this alias exist?" then inserting, as two
separate steps. Under concurrency two requests can both pass the check and both insert. The
fix is a DB-level unique constraint + catching the `IntegrityError` on insert, not an
application-level check. This is the single sharpest lesson in the whole project — reproduce
it (e.g. with a small concurrent-request script) before fixing it, don't just take it on faith.
**Done when:** firing two concurrent requests for the same custom alias results in exactly one
success and one clean 409, never a crash or two rows.

## Stage 5 — Redirect endpoint
**Concepts:** path params, HTTP redirect status codes (301 vs 307 and why it matters here),
early-return validation (expired / disabled / over click limit → 404/410 instead of redirect).
**Build:** `GET /{short_code}` → look up → validate state → redirect.
**Done when:** redirect works, and each failure mode (expired, disabled, max-clicks hit,
not found) returns a distinct, correct status code.

## Stage 6 — Synchronous analytics (the naive version, on purpose)
**Concepts:** reading request metadata (client IP, `User-Agent`, `Referer`), `user-agents`
package for device/browser/OS, `geoip2` + local GeoLite2 DB for country, DB indexing
(index on `link_id` + `clicked_at`).
**Build:** a `Click` model; insert a click row synchronously inside the redirect handler;
measure the added latency this causes.
**Watch out for:** privacy — store a hashed/truncated IP or a derived "unique visitor" token,
not the raw IP, in line with the brief's analytics-privacy requirement.
**Done when:** clicks are recorded correctly, and the user can articulate *why* doing this
synchronously in the redirect path is the wrong long-term shape (this sets up Stage 7-8).

## Stage 7 — Decouple analytics: FastAPI BackgroundTasks
**Concepts:** `BackgroundTasks`, how it differs from `asyncio.create_task`, still same-process.
**Build:** move click logging out of the response path into a background task.
**Done when:** redirect response time no longer includes the analytics write (measurable).

## Stage 8 — Evolve to Redis + a worker process
**Concepts:** producer/consumer pattern, Redis (list or stream) as a queue, a standalone
worker script running its own asyncio event loop, batching writes, graceful shutdown,
handling a worker crash without losing/duplicating too much data.
**Build:** add Redis to `docker-compose.yml`; redirect endpoint pushes a click event to Redis
(fire-and-forget, fast); a separate `worker.py` process consumes events and batch-writes to
Postgres.
**Done when:** the app and worker run as two separate processes, and killing the worker
mid-stream doesn't crash the API.

## Stage 9 — Analytics query endpoints
**Concepts:** aggregate SQL (`GROUP BY`, `date_trunc` for time-bucketed series), avoiding
N+1 queries, authorization (only the link's owner can view its analytics), pagination on
time-series/list results.
**Build:** endpoints for total clicks, unique visitors, clicks-over-time, by country, by
device, by browser, by referrer — all scoped to the authenticated owner.
**Done when:** each endpoint is backed by one efficient query (check with `EXPLAIN`), not a
Python loop over all raw click rows.

## Stage 10 — Rate limiting & hardening
**Concepts:** ASGI middleware, a Redis-backed token-bucket/fixed-window limiter, applying
limits via a dependency/decorator.
**Build:** rate limit `/auth/login`, `/auth/register`, and `POST /links`.
**Done when:** rapid-fire requests past the limit get a clean 429, not a crash or silent drop.

## Stage 11 — Telegram bot
**Concepts:** external service integration, `httpx` for outbound calls, retry/backoff and
isolating a third-party failure from the main app, `aiogram` command handlers as a form of
decorator-based routing, `APScheduler` for daily/weekly scheduled jobs.
**Build:** `/stats`, `/today`, `/week`, `/top` commands calling into the Stage 9 analytics
queries; a scheduled job posting daily/weekly summaries to a configured chat ID.
**Watch out for:** a Telegram API outage or timeout must not affect the main API or the
redirect path — isolate failures, log them, don't let them raise into request handlers.
**Done when:** commands respond correctly, and the bot logs (not crashes on) a simulated
Telegram API failure.

## Stage 12 — Tests, error handling polish, config
**Concepts:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient` for async endpoint tests,
dependency overrides for a test DB, centralized exception handlers
(`@app.exception_handler`), `pydantic-settings` for environment-based config, structured
logging.
**Build:** test coverage for auth, link CRUD, the race-condition fix, and redirect state
transitions; global exception handlers so errors return consistent JSON; settings loaded from
`.env`.
**Done when:** `pytest` passes end-to-end against a test database, and no endpoint can
throw an unhandled 500 for a client-caused error.

---

## Verification approach throughout

At the end of each stage: run the app (and worker/bot once they exist) via
`docker compose up` + `uvicorn`, exercise the new endpoints via `/docs` or `curl`/`httpie`,
and for Stages 4, 6-8 specifically write a tiny script or `pytest` test that proves the
concurrency/latency/failure property the stage is teaching — not just that the happy path
returns 200.

---

## Progress log

- **Stage 0 (done):**
  - [x] venv + `fastapi`/`uvicorn[standard]` installed (`requirements.txt`)
  - [x] `docker-compose.yml` — Postgres 16, host port `5434` (5432/5433 were taken by other
    local projects), healthcheck via `pg_isready`, confirmed `docker compose up -d` reaches
    `healthy`
  - [x] `app = FastAPI()` + `GET /health` route in `app/main.py` — verified 200
    `{"status": "ok"}` via `uvicorn app.main:app --reload`
  - [x] package layout: `app/api`, `app/core`, `app/models`, `app/schemas`, `app/services`,
    `app/db` (plus `app/repositories`, added beyond the plan) — dirs exist, no `__init__.py`
    yet (not blocking, namespace packages work, but worth adding later)

- **Stage 1 (in progress):** FastAPI fundamentals — Pydantic models, path/query params,
  `Depends`.
