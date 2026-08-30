# API Docs

Contract for building a client against the URL Shortener API. Base URL in development: `http://localhost:8000`.

## Auth model

JWT bearer tokens. No refresh tokens, no cookies — the frontend is responsible for storing the `access_token` (e.g. `localStorage`) and attaching it as `Authorization: Bearer <token>` on every authenticated request. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 min server-side); there's no silent refresh, so on a 401 the frontend should drop the token and send the user back to login.

## Error shape

Every error response (auth failures, validation, not-found, conflicts, rate limits, unhandled 500s) has the same envelope:

```json
{ "error_code": "invalid_credentials", "message": "Incorrect email or password." }
```

Match UI behavior on `error_code`, not on `message` text (message strings may change). Known codes are listed per-endpoint below.

## Rate limiting

Some endpoints are rate-limited per client IP. On a 429, the body is `{"error_code": "rate_limit_exceeded", "message": "..."}` — no `Retry-After` header, so just show a generic "too many attempts, try again shortly" message.

---

## Auth

### `POST /api/v1/auth/register`
Rate limited: 5 requests / 60s.

Request:
```json
{ "email": "user@example.com", "password": "MyPassw0rd!" }
```
Password must contain at least one lowercase, one uppercase, and one symbol, min length 8 (enforced by Pydantic — a 422 comes back per-field if violated, standard FastAPI validation error shape, not the `error_code` envelope above).

Response `201`:
```json
{
  "user": { "id": "uuid", "email": "user@example.com", "created_at": "2026-08-30T01:00:00Z" },
  "token": { "access_token": "...", "token_type": "bearer" }
}
```

Errors: `409 user_already_exists`.

### `POST /api/v1/auth/login`
Rate limited: 5 requests / 60s. **Not JSON** — this is FastAPI's `OAuth2PasswordRequestForm`, so send `application/x-www-form-urlencoded` with fields `username` (the email) and `password`.

Response `200`:
```json
{ "access_token": "...", "token_type": "bearer" }
```

Errors: `401 invalid_credentials`.

---

## Users

All endpoints below require `Authorization: Bearer <token>`.

### `GET /api/v1/users/me`
Response `200`:
```json
{ "id": "uuid", "email": "user@example.com", "created_at": "2026-08-30T01:00:00Z", "telegram_linked": false }
```
`telegram_linked` is a derived boolean — the raw Telegram chat ID is never exposed over the API. Use this to drive the "Connect Telegram" button's state (show the link-code flow when `false`, a "connected" badge when `true`). There's still no endpoint to unlink — only linking is currently supported.

### `POST /api/v1/users/telegram-link-code`
Generates a one-time code (valid 5 minutes) the user sends to the Telegram bot as `/link <code>` to connect their chat for `/stats`, `/today`, etc. This is the "Connect Telegram" button's action.

Response `200`:
```json
{ "code": "ESRBMPFG", "expires_in_seconds": 300 }
```

No error codes beyond the standard 401 for a missing/expired token. The UI should show the code with a countdown (or just the raw 5-minute window) and instructions to message the bot.

---

## Links

All endpoints require auth. `link_id` is a UUID.

### `POST /api/v1/links`
Rate limited: 20 requests / 60s.

Request:
```json
{
  "original_url": "https://example.com/some/long/path",
  "custom_alias": "my-alias",      // optional, 3-32 chars, [a-zA-Z0-9_-], lowercased server-side
  "max_clicks": 100,               // optional, > 0
  "expires_at": "2026-12-01T00:00:00Z"  // optional, must be in the future
}
```

Response `201` — `LinkResponse` (see shape below).

Errors: `409 alias_already_exists`, `422` (Pydantic validation, e.g. reserved alias, past expiry).

### `GET /api/v1/links?skip=0&limit=20`
List the current user's own links (`skip` ≥ 0, `limit` 1–100, default 20). Response `200`: `LinkResponse[]`.

### `GET /api/v1/links/{link_id}`
Response `200`: `LinkResponse`. Errors: `404 link_not_found` (also returned if the link exists but belongs to another user — ownership is not distinguished from non-existence).

### `PATCH /api/v1/links/{link_id}`
Partial update — send only the fields you want to change.

Request (all optional):
```json
{ "original_url": "https://...", "max_clicks": 50, "expires_at": "2026-12-01T00:00:00Z", "is_active": false }
```
Note: extra/unknown fields are rejected (`extra="forbid"`) — don't send fields the schema doesn't define.

Response `200`: `LinkResponse`. Errors: `404 link_not_found`, `422`.

### `POST /api/v1/links/{link_id}/activate`
### `POST /api/v1/links/{link_id}/deactivate`
No body. Response `200`: `LinkResponse`. Errors: `404 link_not_found`, and activate can fail with `409 link_expired` or `409 click_limit_reached` if those conditions are already true.

### `DELETE /api/v1/links/{link_id}`
No body. Response `204`. Errors: `404 link_not_found`.

### `LinkResponse` shape
```json
{
  "id": "uuid",
  "short_code": "aB3xY9",
  "short_url": "http://localhost:8000/aB3xY9",
  "original_url": "https://example.com/...",
  "expires_at": "2026-12-01T00:00:00Z",
  "max_clicks": 100,
  "click_count": 12,
  "is_active": true,
  "created_at": "2026-08-30T01:00:00Z"
}
```
`short_url` is server-computed (`BASE_URL` + `short_code`) — use it directly, don't reconstruct it client-side.

---

## Analytics

All under `/api/v1/links/{link_id}/analytics/...`, all require auth and link ownership (`404 link_not_found` if not owned/doesn't exist).

| Endpoint | Response |
|---|---|
| `GET .../summary` | `{ "total_clicks": int, "unique_visitors": int }` |
| `GET .../timeseries` | `[{ "date": datetime, "count": int }, ...]` |
| `GET .../countries` | `[{ "country": string\|null, "count": int }, ...]` |
| `GET .../devices` | `[{ "device_type": string\|null, "count": int }, ...]` |
| `GET .../browsers` | `[{ "browser": string\|null, "count": int }, ...]` |
| `GET .../referrers` | `[{ "referer": string\|null, "count": int }, ...]` |

`null` values mean "unknown" (e.g. no `Referer` header, unparseable user agent) — render as "Unknown" / "Direct" rather than blank.

---

## Redirect (public, no auth)

`GET /{short_code}` — not under `/api/v1`, this is the actual shortlink a visitor clicks. It 307-redirects to `original_url`, or errors as:

- `404 link_not_found`
- `410 link_is_not_active`
- `410 link_unavailable` (expired or click-limit reached, evaluated at click time even if not yet auto-deactivated)

The frontend won't call this directly (browsers navigate to it), but should surface these states nicely when showing a link's own detail page — e.g. don't just display "inactive," check `is_active` alongside `expires_at`/`max_clicks` vs `click_count` to explain *why*.

---

## Health check (public, no auth)

`GET /health` → `{ "status": "ok"|"degraded", "database": "ok"|"error", "uptime_seconds": float, "timestamp": iso8601 }`, `200` or `503`. Useful for an admin/status widget, not part of the normal user flow.

