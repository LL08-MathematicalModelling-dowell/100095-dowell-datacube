# Datacube backend — API guide for frontends

This document is for **web and mobile clients** integrating with the Datacube Django API: base URLs, authentication, roles, and every HTTP surface the UI typically needs.

For local environment variables and ops, see the repo [`README.md`](../README.md) and [`.env.example`](../.env.example).

---

## 1. Base URLs

All paths below are **relative to your API host** (e.g. `https://datacube.example.com`). Replace `API_BASE` with that origin (no trailing slash required; most routes allow an optional trailing slash).

| Prefix | Purpose |
|--------|---------|
| `API_BASE/api/v2/` | **Data API** — databases, CRUD, files, health |
| `API_BASE/core/` | **Auth & account** — login, JWT, profile, API keys, OAuth, OTP |
| `API_BASE/analytics/api/v2/` | **Analytics** — dashboard metrics (JWT) |
| `API_BASE/admin/` | Django admin (browser) — not used by SPA auth flow |

**Examples**

- Health: `GET API_BASE/api/v2/health_check/`
- Login: `POST API_BASE/core/login/`
- CRUD: `POST API_BASE/api/v2/crud/`

---

## 2. Conventions

### 2.1 HTTP and JSON

- Use **`Content-Type: application/json`** for JSON bodies.
- Responses are JSON unless documented otherwise (e.g. file download/stream).
- **MongoDB ObjectIds** in JSON are **24-character hex strings** (e.g. `507f1f77bcf86cd799439011`).

### 2.2 Trailing slashes

Routes are defined with **optional trailing slash** (`…/?$`). Both `.../crud` and `.../crud/` work.

### 2.3 CORS (typical production setup)

`CORS_ALLOW_ALL_ORIGINS` may be enabled for `/api/*` in production settings — confirm with your deployment. Send **authenticated** requests with `Authorization` headers as below.

### 2.4 Errors

Validation errors often look like DRF field errors:

```json
{ "email": ["This field is required."] }
```

or

```json
{ "error": "Invalid credentials" }
```

Check the HTTP status: **400** validation, **401** auth failed, **403** forbidden (role, quota, unverified email), **404** not found.

---

## 3. Authentication

### 3.1 JWT (primary)

After login (or OTP/OAuth verify), the API returns **`access`** and **`refresh`** tokens (strings).

**Send on each request:**

```http
Authorization: Bearer <access_token>
```

**Access token lifetime** (defaults in code): on the order of **days**; **`refresh`** is longer-lived. When `access` expires, call refresh (see [§4.5](#45-token-refresh)).

**Who can use JWT?**

The backend resolves the user from MongoDB and **requires a verified email** for API access. Unverified users get **403** with `code: "email_unverified"` on login until they complete verification (OTP or legacy link).

### 3.2 API keys (machine / script clients)

Users can create keys **after** they are logged in (see [§4.10](#410-api-keys-jwt-only)).

**Header:**

```http
Authorization: Api-Key <full_key_string>
```

The key format stored is like `sk_test_...`. **Email must still be verified** for the key to work.

### 3.3 Demo login (non-production / playground)

If enabled on the server, **`POST /core/api/v2/demo/login/`** returns JWTs for a fixed demo user **without a password** (see core URLs). Use only where explicitly deployed.

---

## 4. Auth & account API (`/core/`)

Unless noted, bodies are JSON.

### 4.1 Register (email + password)

`POST /core/register/`

```json
{
  "email": "user@example.com",
  "firstName": "Ada",
  "lastName": "Lovelace",
  "password": "minimum8chars"
}
```

**201** — User created; OTP sent for verification (check email). Stripe customer creation may run server-side (non-fatal if misconfigured).

### 4.2 Register (email-only / passwordless path)

`POST /core/auth/register/email-only/`

```json
{ "email": "user@example.com", "firstName": "", "lastName": "" }
```

**201** — OTP emailed to complete registration.

### 4.3 Request OTP

`POST /core/auth/otp/request/`

```json
{ "email": "user@example.com", "purpose": "register" }
```

`purpose`: **`register`** | **`login_email`**

Response is intentionally vague (“If an account matches…”) to avoid email enumeration.

### 4.4 Verify OTP → JWT

`POST /core/auth/otp/verify/`

```json
{
  "email": "user@example.com",
  "code": "123456",
  "purpose": "register"
}
```

**200** — Same shape as password login:

```json
{
  "refresh": "...",
  "access": "...",
  "firstName": "...",
  "lastName": "...",
  "role": "developer",
  "email_verified": true
}
```

### 4.5 Token refresh

`POST /core/auth/token/refresh/`

```json
{ "refresh": "<refresh_token>" }
```

**200**

```json
{ "access": "<new_access_token>" }
```

(Refresh rotation/blacklist is off by design for Mongo-backed users.)

### 4.6 Login (password)

`POST /core/login/`

```json
{ "email": "user@example.com", "password": "..." }
```

**200** — `refresh`, `access`, `firstName`, `lastName`, `role`, `email_verified`.

**401** — bad password.

**403** — `email_unverified`: must complete OTP/verification first.

### 4.7 OAuth (Google / GitHub, PKCE)

Server exchanges the **authorization code** (not an ID token from the client).

`POST /core/auth/oauth/google/`

```json
{
  "code": "<from Google redirect>",
  "code_verifier": "<PKCE verifier>",
  "redirect_uri": "https://your-app.example/oauth/callback"
}
```

`POST /core/auth/oauth/github/` — same JSON shape.

**200** — Same token + profile fields as login. **503** if OAuth env not configured.

### 4.8 Resend registration OTP

`POST /core/verify-email/resend/`

```json
{ "email": "user@example.com" }
```

### 4.9 Email link verification (legacy GET)

`GET /core/verify-email/<token>/`

**200** `{ "message": "Email verified successfully!" }` or **400** if invalid/expired.

### 4.10 Password reset (OTP via email)

**Request code:** `POST /core/password-reset/request/` — `{ "email": "..." }`  
**Confirm:** `POST /core/password-reset/confirm/` — `{ "email", "code", "password" }` (`password` min length 8)

### 4.11 Profile

`GET /core/profile/` — JWT → user document fields (`id`, `email`, `firstName`, `lastName`, `role`, `is_email_verified`, `auth_method`, `has_avatar`).

`PATCH /core/profile/` — `{ "firstName": "...", "lastName": "..." }` (optional fields)

### 4.12 Avatar

`GET /core/profile/avatar/` — binary image or **404**.

`POST /core/profile/avatar/` — `multipart/form-data`, field **`file`**. Allowed types: jpeg, png, webp, gif; max **3 MB**.

`DELETE /core/profile/avatar/` — remove stored avatar; **204** on success.

### 4.13 Account delete (soft delete)

`DELETE /core/account/` — JWT; **204** on success.

### 4.14 API keys (JWT only)

`GET /core/api/v1/keys/` — JSON **array** of key metadata (no full secret repeated).

`POST /core/api/v1/keys/` — `{ "name": "My integration" }`  

**201** — `{ "key": "sk_test_...", "name": "My integration" }` — the **`key`** string is shown **once**; store it securely.

`DELETE /core/api/v1/keys/<key_id>/` — revoke (`key_id` is the Mongo id string).

### 4.15 Admin: set user role

`POST /core/admin/users/role/` — JWT, **`admin`** role only.

```json
{ "email": "user@example.com", "role": "developer" }
```

Roles: **`admin`**, **`analyst`**, **`developer`** (`user` in the serializer is normalized to developer).

### 4.16 Dashboard v1 helpers (JWT)

- `GET /core/api/v1/dashboard/stats/`
- `GET /core/api/v1/database/<db_id>/`

(Exact response shapes: inspect network tab or backend serializers/views.)

---

## 5. Data API (`/api/v2/`)

**Default:** `IsAuthenticated` + role rules (see [§6](#6-roles-and-permissions)). **Health** is public.

### 5.1 Health

`GET /api/v2/health_check/` — no auth.

### 5.2 Create database

`POST /api/v2/create_database/` — **developer or admin** only.

```json
{
  "db_name": "my_app",
  "collections": [
    {
      "name": "users",
      "fields": [{ "name": "email", "type": "string" }]
    }
  ]
}
```

### 5.3 Add collections

`POST /api/v2/add_collection/` — **developer or admin**.

```json
{
  "database_id": "<24_hex_objectid>",
  "collections": [{ "name": "orders", "fields": [...] }]
}
```

### 5.4 List databases

`GET /api/v2/list_databases/?page=1&page_size=50&search=`

Query params use `ListQuerySerializer`: optional **`filters`** (JSON) not used here; **`page`**, **`page_size`** (max 1000), optional **`search`**.

### 5.5 List collections

`GET /api/v2/list_collections/?database_id=<24_hex_objectid>`

### 5.6 Get metadata

`GET /api/v2/get_metadata/?database_id=<24_hex_objectid>`

### 5.7 Drop database

`DELETE /api/v2/drop_database/` — **developer or admin**.

```json
{
  "database_id": "<24_hex_objectid>",
  "confirmation": "<must match database displayName exactly, case-insensitive>"
}
```

### 5.8 Drop collections

`DELETE /api/v2/drop_collections/` — **developer or admin**.

```json
{
  "database_id": "<24_hex_objectid>",
  "collection_names": ["coll_a", "coll_b"]
}
```

### 5.9 Import JSON file

`POST /api/v2/import_data/` — **developer or admin**, `multipart/form-data`: **`json_file`** (file), **`database_id`**, optional **`collection_name`**.

### 5.10 Prune field metadata

`POST /api/v2/admin/prune_fields/` — **`admin`** only.

```json
{ "database_id": "<24_hex_objectid>", "dry_run": true }
```

`dry_run` defaults to **`true`** if omitted (preview); set **`false`** to apply changes. Response body is the `result` dict from the metadata service.

### 5.11 CRUD (single endpoint)

`POST | GET | PUT | DELETE /api/v2/crud/`

**Analyst** may only use **safe** methods (**GET**). **Developer/admin** may write.

**Safety rules (PUT/DELETE):**

- `filters` must be a **non-empty** object.
- Default (single) update: `filters` must include **`_id`** or **`id`**.
- Multi-document update: set **`update_many`: true** (filters still required, e.g. `{ "status": "pending" }`).
- Dangerous filter operators (e.g. `$where`) are rejected.
- Unknown DB/collection → **403** (not 500).

#### Insert — `POST`

```json
{
  "database_id": "<24_hex_objectid>",
  "collection_name": "users",
  "documents": [{ "username": "alice" }, { "username": "bob" }]
}
```

| Limit | Value |
|-------|--------|
| Max documents per request | **500** |

**201** — `{ "success": true, "inserted_ids": ["..."] }`  
**403** — storage quota exceeded.

#### Query — `GET`

Query string parameters:

| Param | Description |
|-------|-------------|
| `database_id` | Required |
| `collection_name` | Required |
| `filters` | Optional JSON object (Mongo filter); omit or `{}` for all active rows |
| `page` | Default 1 |
| `page_size` | Default 50, max 1000 |

Soft-deleted documents (`is_deleted: true`) are excluded from results.

**200** — `{ "success", "data", "pagination": { "page", "page_size", "total_items", "total_pages" } }`

#### Update — `PUT`

```json
{
  "database_id": "<24_hex_objectid>",
  "collection_name": "users",
  "filters": { "_id": "<24_hex_objectid>" },
  "update_data": { "status": "active" },
  "update_all_fields": true,
  "update_many": false,
  "upsert": false
}
```

| Field | Default | Meaning |
|-------|---------|---------|
| `update_data` | — | Plain field map **or** allowed operators (`$set`, `$inc`, `$unset`, …) |
| `update_all_fields` | `false` | `true`: full `$set`/operators (may add fields). `false`: only change fields that already exist on each doc |
| `update_many` | `false` | `true`: apply the **same** update to **all** matches for **one** filter; `false`: single-document (requires `_id`/`id` in filters) |
| `upsert` | `false` | With `_id`/`id` filter, create document if none matches (`update_many` must be `false`) |

**`upsert` + `update_many`:** not supported. MongoDB `updateMany` + `upsert` inserts at most one document when zero rows match — it cannot update some rows and insert others from a list. Use **bulk update** (below) for that pattern.

**Examples**

- Patch one field on one doc (UI-friendly):

```json
{
  "filters": { "_id": "674a1b2c3d4e5f6789012345" },
  "update_data": { "status": "active" },
  "update_all_fields": true
}
```

- Operator update:

```json
{
  "filters": { "_id": "674a1b2c3d4e5f6789012345" },
  "update_data": { "$set": { "status": "active" }, "$inc": { "login_count": 1 } },
  "update_all_fields": true
}
```

- Upsert by id:

```json
{
  "filters": { "_id": "674a1b2c3d4e5f6789012345" },
  "update_data": { "username": "alice", "status": "active" },
  "update_all_fields": true,
  "upsert": true
}
```

**200** — `{ "success": true, "modified_count": n, "matched_count": m, "upserted_id": "..." }`  
`upserted_id` is present only when a new document was inserted.

#### Bulk update / upsert — `POST /api/v2/crud/bulk/`

Use when you have **multiple documents** and each may need its own update or upsert (e.g. sync loyalty points for many users). One network round-trip via MongoDB `bulkWrite`.

```json
{
  "database_id": "<24_hex_objectid>",
  "collection_name": "users",
  "operations": [
    {
      "filters": { "_id": "674a1b2c3d4e5f6789012345" },
      "update_data": { "points": 120 },
      "update_all_fields": true,
      "upsert": true
    },
    {
      "filters": { "_id": "674a1b2c3d4e5f6789012346" },
      "update_data": { "points": 450 },
      "update_all_fields": true,
      "upsert": true
    }
  ]
}
```

| Field | Default | Meaning |
|-------|---------|---------|
| `operations` | — | **1–500** items; each runs as `updateOne` |
| `filters` | — | Required; must include `_id` or `id` |
| `update_all_fields` | `false` | Same as PUT; **`upsert` requires `true`** |
| `upsert` | `false` | Insert when no active document matches |

**200** example:

```json
{
  "success": true,
  "matched_count": 1,
  "modified_count": 1,
  "upserted_count": 1,
  "results": [
    { "index": 0, "ok": true },
    { "index": 1, "ok": true, "upserted_id": "674a1b2c3d4e5f6789012347" }
  ]
}
```

If some operations fail (`ordered: false`), successful ops still apply; failed indices appear in `errors`.

#### Delete — `DELETE`

```json
{
  "database_id": "<24_hex_objectid>",
  "collection_name": "users",
  "filters": { "status": "archived" },
  "soft_delete": true
}
```

`filters` must be **non-empty**. `soft_delete` **true** (default): sets `is_deleted` and `deleted_at` on active rows; **false**: permanently removes matching documents (any `is_deleted` state).

**200** — `{ "success": true, "count": n }`

### 5.12 Files (GridFS)

**List** — `GET /api/v2/files/?page=1&page_size=50&search=` (pagination + optional search).

**Upload** — `POST /api/v2/files/` as **`multipart/form-data`**:

| Field | Required | Notes |
|-------|----------|--------|
| `file` | Yes | Binary upload |
| `filename` | No | Display name |
| `content_type` | No | MIME type |

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/api/v2/files/` | Paginated list (often includes signed URLs) |
| `POST` | `/api/v2/files/` | Upload |
| `GET` | `/api/v2/files/<file_id>/` | Metadata |
| `DELETE` | `/api/v2/files/<file_id>/` | Delete |
| `GET` | `/api/v2/files/stream/<file_id>/` | Streaming body |
| `GET` | `/api/v2/files/download/<file_id>/` | Full download |

`<file_id>` is 24 hex chars.

Some stream/download flows validate **signed URLs** — use the links returned by list/detail responses when provided.

---

## 6. Roles and permissions

| Role | Typical use |
|------|-------------|
| **developer** | Full data API reads/writes (default for most users). |
| **analyst** | **Read-only** on CRUD/files/list paths that use `BlockAnalystOnUnsafeMethods` (no POST/PUT/PATCH/DELETE on those resources). |
| **admin** | Same as developer for data APIs, plus **admin-only** routes (e.g. **prune_fields**, **set user role**). |

JWT and API keys both resolve to a `MongoUser` with **`role`** — use it in the UI to hide destructive actions.

---

## 7. Analytics API (`/analytics/api/v2/`)

All endpoints: **JWT required** (`Authorization: Bearer …`).

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `dashboard/` | Overview, 7-day stats |
| `GET` | `performance/` | Latency percentiles + throughput |
| `GET` | `errors/` | Error breakdown |
| `GET` | `top-collections/` | Hot collections |
| `GET` | `slow-queries/` | Slow query log |
| `GET` | `endpoint-volume/` | Traffic by path |
| `GET` | `operation-breakdown/` | DB op mix |
| `GET` | `storage-trend/` | Storage over time |

Responses are JSON with `success: true` and domain-specific keys (`overview`, `percentiles_ms`, etc.). Optional query params (e.g. pagination on `slow-queries`) are documented in `analytics/views/analytics_views.py`.

---

## 8. Rate limiting (auth endpoints)

DRF throttles apply to sensitive **anonymous** routes (login, register, OAuth, refresh, demo login, password reset, OTP). If you receive **429 Too Many Requests**, back off exponentially and avoid tight retry loops.

---

## 9. Minimal integration checklist

1. **Store** `access` + `refresh` securely (memory + secure storage on mobile; `httpOnly` cookies only if you add a BFF — not default here).
2. **Attach** `Authorization: Bearer` on **data**, **analytics**, and **profile** calls.
3. **Refresh** access token before expiry; on **401**, try **one** refresh then force re-login.
4. **Gate** the app on **`email_verified`** / `is_email_verified` from login/profile.
5. **Respect** **analyst** read-only: hide create/update/delete in the UI.
6. Use **`documents`** (not `data`) in **CRUD POST** payloads.

---

## 10. Related files in this repo

| Topic | Location |
|-------|----------|
| Data routes | `api/presentation/urls_v2.py` |
| Auth routes | `core/presentation/urls.py` |
| Serializers / payloads | `api/presentation/serializers.py`, `core/presentation/serializers.py` |
| JWT + API key auth | `core/infrastructure/authentication.py` |
| Analytics routes | `analytics/urls.py` |

This guide is meant to stay **human-readable**; for exhaustive field-level OpenAPI you could generate a schema later from DRF (optional).
