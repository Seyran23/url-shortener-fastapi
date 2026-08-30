# Shortly — URL Shortener API

A production-shaped URL shortener built with FastAPI. Started as a Python-learning project; ended up with real auth, per-link click analytics with geo/device/browser breakdowns, rate limiting, and a Telegram bot that multiple users can link to their own accounts.

## Features

- **Auth** — email/password registration and login, JWT bearer tokens, Argon2 password hashing
- **Link management** — create short links with optional custom alias, expiry date, and max-click limit; activate/deactivate/delete; all scoped to the owning user
- **Click analytics** — every redirect is logged asynchronously (doesn't block the redirect) with geo-located country, parsed browser/OS/device type, and referrer; queryable as a summary, a daily timeseries, and per-dimension breakdowns
- **Rate limiting** — Redis-backed, per-IP, applied to auth and link-creation endpoints
- **Telegram bot** — multi-user. Each account links its own chat via a one-time code (`/link <code>`, valid 5 minutes) generated from the API; linked chats can query `/stats`, `/today`, `/week`, `/top`, `/breakdown`, and receive scheduled daily/weekly reports
- **Structured errors** — every failure mode returns a consistent `{error_code, message}` envelope 

## Tech stack

| Layer | Choice |
|---|---|
| API | FastAPI + Uvicorn |
| DB | PostgreSQL, async SQLAlchemy 2.0, asyncpg, Alembic migrations |
| Cache / ephemeral state | Redis (rate-limit counters, one-time Telegram link codes) |
| Auth | JWT (python-jose), Argon2 (passlib) |
| Bot | aiogram 3, APScheduler (daily/weekly report jobs) |
| Geo lookup | MaxMind GeoLite2 (`geoip2`) |
| Tests | pytest + pytest-asyncio, against a dedicated test database |

## Architecture

Layered, one direction of dependency: **route → service → repository → model**. Routes handle HTTP concerns and auth dependencies only; services hold business logic and raise typed `AppError` subclasses; repositories are the only layer that touches SQLAlchemy queries directly.

```
app/
  api/            route handlers (v1/ for the authenticated API, health.py, redirect.py for the public shortlink)
  core/           config, JWT/password helpers, Redis client, rate limiter, geo lookup, centralized constants/exceptions
  db/             session/engine setup, Alembic migrations
  models/         SQLAlchemy ORM models (User, Link, Analytics)
  repositories/   query layer, one module per model
  schemas/        Pydantic request/response models
  services/       business logic layer
  telegram/       aiogram bot: command handlers, per-chat auth, message formatters
```

Errors are domain-specific exceptions (`LinkNotFoundError`, `AliasAlreadyExistsError`, `RateLimitExceededError`, ...) defined in `app/core/exceptions.py`, caught by a single global handler in `app/main.py` that maps them to their declared HTTP status code — routes and services never construct `JSONResponse`s by hand.

## Getting started

**Prerequisites:** Python 3.12+, Docker (for Postgres/Redis), a Telegram bot token from [@BotFather](https://t.me/BotFather) if you want the bot.

```bash
# 1. Start Postgres + Redis
docker compose up -d

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# fill in DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM (e.g. HS256),
# ACCESS_TOKEN_EXPIRE_MINUTES, and TELEGRAM_BOT_TOKEN if using the bot

# 4. Run migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload --port 8000

# 6. (Optional) start the Telegram bot, in a separate terminal
python -m app.telegram.bot
```

API docs (Swagger UI): `http://localhost:8000/docs`.

### Geo lookups

In `ENVIRONMENT=development` (the default), country resolution is faked with a random sample — no database file needed. For real lookups, download `GeoLite2-Country.mmdb` from MaxMind and place it at the project root.

## Testing

```bash
pytest
```

Runs against `TEST_DATABASE_URL`, a separate database from your dev one (see `tests/conftest.py`). A hand-rolled concurrency/latency stress test is also included:

```bash
python scripts/stress_test.py --url http://127.0.0.1:8000/<short_code> --requests 500 --concurrency 50
```

## API reference

Full endpoint-by-endpoint contract — request/response shapes, auth flow, error codes, rate limits — is in [docs/api-guide.md](docs/api-guide.md). Interactive docs are also served at `/docs` while the app is running.

## Frontend

The frontend lives in a separate (private) repository, built to consume this API per the guide above. Screenshots of it are in [screenshots/](screenshots/) for reference:

- Auth: login and registration, including validation and error states
- Dashboard: empty state, link list, create-link modal (with alias-conflict handling)
- Link detail: analytics (clicks over time, countries, devices, browsers, referrers), inline editing, deactivated/limit-reached states
- Settings: account info, Telegram connect flow (one-time code display)
- 404 page
- Telegram bot: linking a chat, the command menu, and `/stats`, `/breakdown`, `/week`, `/help`, `/top`, `/today` in action

## Telegram bot

Linking is per-account, not a single hardcoded owner: a user generates a one-time code via `POST /api/v1/users/telegram-link-code` (see the Settings screenshots above), then sends `/link <code>` to the bot to connect their chat. From then on that chat's commands resolve to their own data:

| Command | Description |
|---|---|
| `/link <code>` | Connect this chat to your account |
| `/stats` | Overall totals |
| `/today` / `/week` | Period totals + top links |
| `/top` | Top links by clicks |
| `/breakdown` | Countries, devices, browsers, referrers |
| `/help` | List commands |

The bot also pushes scheduled daily (09:00) and weekly (Monday 09:00) reports to every linked chat.

