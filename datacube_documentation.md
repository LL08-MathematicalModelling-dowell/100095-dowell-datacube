# Datacube — platform documentation

Complete reference for the **Datacube V2** monorepo: architecture, configuration, authentication, every HTTP API surface, roles, and client integration patterns.

For a **curated developer subset** with copy-paste samples (cURL, Python, TypeScript, JavaScript), use the in-app **API reference** at `/api-docs` in the React UI or the data file `UI/datacube-UI/src/data/apiReference.ts`.

For SPA-specific auth flows, see also [`backend/docs/FRONTEND_API_GUIDE.md`](backend/docs/FRONTEND_API_GUIDE.md).

---

## Table of contents

1. [Overview](#1-overview)
2. [Repository layout](#2-repository-layout)
3. [Architecture](#3-architecture)
4. [Configuration](#4-configuration)
5. [HTTP surface](#5-http-surface)
6. [Conventions](#6-conventions)
7. [Authentication & account (`/core/`)](#7-authentication--account-core)
8. [Data API (`/api/v2/`)](#8-data-api-apiv2)
9. [Analytics API (`/analytics/api/v2/`)](#9-analytics-api-analyticsapiv2)
10. [Roles & permissions](#10-roles--permissions)
11. [Errors & rate limits](#11-errors--rate-limits)
12. [Frontend application](#12-frontend-application)
13. [Local development & testing](#13-local-development--testing)
14. [Integration checklist](#14-integration-checklist)
15. [Related source files](#15-related-source-files)

---

## 1. Overview

**Datacube** is a MongoDB-backed database and document platform:

- **Django REST Framework** backend with layered apps (`api`, `core`, `analytics`)
- **JWT** and **API key** authentication stored in MongoDB
- **Logical databases** with collection metadata, field typing, and quotas
- **Unified CRUD** endpoint for document operations
- **GridFS** file storage for arbitrary binaries
- **React** dashboard for operators and account management
- Optional **analytics** middleware and dashboard metrics

ObjectIds in JSON are always **24-character hexadecimal strings**.

---

## 2. Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | Django project (`api`, `core`, `analytics`, `project`) |
| `UI/datacube-UI/` | React + Vite SPA (dashboard, auth, API docs) |
| `datacube_documentation.md` | This file — full platform reference |
| `backend/docs/FRONTEND_API_GUIDE.md` | SPA-focused API guide |
| `backend/.env.example` | Environment variable template |
| `_frontend_old_nextjs/`, `_Datacube_api_libraries_old/` | Legacy snapshots (not active) |

---

## 3. Architecture

Django apps keep historical names for migrations. Code is organized by **layer** inside each app.

### 3.1 `api` — data plane

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Presentation | `api.presentation` | DRF views, serializers, `urls_v2.py` |
| Application | `api.application` | Metadata, databases, collections, documents, GridFS services |
| Infrastructure | `api.infrastructure` | Mongo helpers, naming, signed URLs, validators |
| Cross-cutting | `api/` root | `middleware.py`, `permissions.py`, `models.py` |

Views inherit from `BaseAPIView` in `api.presentation.views.base` (analytics hooks, shared errors).

### 3.2 `core` — accounts & keys

| Layer | Package |
|-------|---------|
| Presentation | `core.presentation` — auth views, profile, API keys, URLs |
| Infrastructure | `core.infrastructure` — JWT, `MongoUser`, user managers, OTP, OAuth PKCE |

DRF uses `CustomJWTAuthentication` and `APIKeyAuthentication` from `core.infrastructure.authentication`.

### 3.3 `analytics`

Usage logging middleware and read-only dashboard APIs under `/analytics/api/v2/`.

---

## 4. Configuration

Required environment variables (see `backend/project/settings/common.py` and `.env.example`):

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret (per environment) |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DATABASE` | Metadata catalog database name |
| `MONGODB_COLLECTION` | Metadata collection for database registry |
| `AUTH_DB_NAME` | Users, API keys, OTP |
| `FILE_STORAGE_DB_NAME` | GridFS files + avatars bucket |

Optional: Stripe, OAuth client IDs, demo login, email SMTP — read from settings modules where used.

**Settings module:** `project.settings.development` by default (`manage.py`); override with `DJANGO_SETTINGS_MODULE` for production.

---

## 5. HTTP surface

Mounted in `backend/project/urls.py`:

| Prefix | App | Purpose |
|--------|-----|---------|
| `/api/v2/` | `api` | Databases, CRUD, files, health |
| `/core/` | `core` | Auth, profile, API keys |
| `/analytics/api/v2/` | `analytics` | Dashboard metrics |
| `/admin/` | Django | Admin site |

Replace `https://<host>` in examples with your deployment origin (`API_BASE`).

---

## 6. Conventions

### 6.1 JSON

- Request: `Content-Type: application/json` unless multipart.
- Responses are JSON except file stream/download and avatar binary.

### 6.2 Trailing slashes

Routes accept optional trailing slash (`/crud` and `/crud/` both work).

### 6.3 Pagination

List endpoints use `page` (default 1) and `page_size` (default 50, max 1000 unless noted).

### 6.4 Soft delete (documents)

CRUD queries exclude `is_deleted: true` by default. DELETE with `soft_delete: true` (default) sets `is_deleted` and `deleted_at`.

### 6.5 Collection field types

Allowed in metadata: `string`, `number`, `object`, `array`, `boolean`, `date`, `null`, `binary`, `objectid`, `decimal128`, `regex`, `timestamp`.

---

## 7. Authentication & account (`/core/`)

### 7.1 JWT (primary)

After login, OTP verify, or OAuth:

```http
Authorization: Bearer <access_token>
```

Login returns `access`, `refresh`, `firstName`, `lastName`, `role`, `email_verified`.

**Refresh:** `POST /core/auth/token/refresh/` — `{ "refresh": "<token>" }` → `{ "access": "…" }`.

**Verified email required** for data API access. Unverified login may return **403** with `code: "email_unverified"`.

### 7.2 API keys

Created while authenticated:

```http
Authorization: Api-Key sk_test_…
```

`POST /core/api/v1/keys/` — `{ "name": "…" }` returns full `key` **once**.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/core/api/v1/keys/` | List key metadata |
| POST | `/core/api/v1/keys/` | Create key |
| DELETE | `/core/api/v1/keys/<key_id>/` | Revoke |

### 7.3 Registration & verification

| Method | Path | Description |
|--------|------|-------------|
| POST | `/core/register/` | Email + password; OTP sent |
| POST | `/core/auth/register/email-only/` | Passwordless registration path |
| POST | `/core/auth/otp/request/` | `{ email, purpose: "register" \| "login_email" }` |
| POST | `/core/auth/otp/verify/` | Returns JWTs on success |
| GET | `/core/verify-email/<token>/` | Legacy link verification |
| POST | `/core/verify-email/resend/` | Resend verification (JWT) |

### 7.4 OAuth (PKCE)

| Method | Path |
|--------|------|
| POST | `/core/auth/oauth/google/` |
| POST | `/core/auth/oauth/github/` |

Body: `{ "code", "code_verifier", "redirect_uri" }` — server exchanges code; returns JWTs.

### 7.5 Password reset

| Method | Path |
|--------|------|
| POST | `/core/password-reset/request/` | `{ "email" }` |
| POST | `/core/password-reset/confirm/` | `{ "email", "code", "password" }` (min 8 chars) |

### 7.6 Profile & account

| Method | Path | Description |
|--------|------|-------------|
| GET | `/core/profile/` | User profile (`id`, `email`, `firstName`, `lastName`, `role`, `is_email_verified`, `auth_method`, `has_avatar`) |
| PATCH | `/core/profile/` | `{ "firstName", "lastName" }` |
| GET | `/core/profile/avatar/` | Binary image or 404 |
| POST | `/core/profile/avatar/` | Multipart field `file` (jpeg/png/webp/gif, max 3 MB) |
| DELETE | `/core/profile/avatar/` | Remove avatar |
| DELETE | `/core/account/` | Soft-delete account (204) |

Profile avatars use a dedicated GridFS bucket — **not** `/api/v2/files/`.

### 7.7 Admin & legacy v1

| Method | Path | Auth |
|--------|------|------|
| POST | `/core/admin/users/role/` | Admin — `{ "email", "role" }` |
| GET | `/core/api/v1/dashboard/stats/` | JWT |
| GET | `/core/api/v1/database/<db_id>/` | JWT |
| POST | `/core/api/v2/demo/login/` | Non-prod demo JWTs (if enabled) |

Roles: `admin`, `analyst`, `developer` (`user` normalized to developer).

---

## 8. Data API (`/api/v2/`)

Default: authenticated. **Health** is public.

### 8.1 Health

`GET /api/v2/health_check/` — no auth.

```json
{ "success": true, "status": "healthy", "timestamp": "…" }
```

### 8.2 Databases & metadata

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | `/api/v2/create_database/` | developer/admin | Create DB + collections |
| GET | `/api/v2/list_databases/` | all | `?page=&page_size=&search=` |
| GET | `/api/v2/list_collections/` | all | `?database_id=` |
| GET | `/api/v2/get_metadata/` | all | Full metadata doc |
| POST | `/api/v2/add_collection/` | developer/admin | Add collections to DB |
| DELETE | `/api/v2/drop_database/` | developer/admin | Requires `confirmation` = displayName |
| DELETE | `/api/v2/drop_collections/` | developer/admin | `{ database_id, collection_names[] }` |
| POST | `/api/v2/import_data/` | developer/admin | Multipart: `json_file`, `database_id`, optional `collection_name` |
| POST | `/api/v2/admin/prune_fields/` | admin | `{ database_id, dry_run }` — metadata cleanup |

**Create database example:**

```json
{
  "db_name": "my_app",
  "collections": [
    { "name": "users", "fields": [{ "name": "email", "type": "string" }] }
  ]
}
```

### 8.3 CRUD (`/api/v2/crud/`)

Single endpoint: **POST | GET | PUT | DELETE**.

**Analyst:** GET only. **Developer/admin:** all methods.

#### Insert — POST

```json
{
  "database_id": "<24_hex>",
  "collection_name": "users",
  "documents": [{ "email": "a@example.com" }]
}
```

Max **500** documents per request. Use `documents`, not `data`.

**201** — `{ "success": true, "inserted_ids": ["…"] }`

#### Query — GET

| Param | Required | Notes |
|-------|----------|-------|
| `database_id` | yes | |
| `collection_name` | yes | |
| `filters` | no | JSON object string |
| `page`, `page_size` | no | Defaults 1 / 50 |

**200** — `{ "success", "data", "pagination" }`

#### Update — PUT

```json
{
  "database_id": "<24_hex>",
  "collection_name": "users",
  "filters": { "_id": "<24_hex>" },
  "update_data": { "status": "active" },
  "update_all_fields": true,
  "update_many": false,
  "upsert": false
}
```

| Field | Default | Meaning |
|-------|---------|---------|
| `update_all_fields` | false | true: may add fields; false: patch existing fields only |
| `update_many` | false | true: update all matches; false: single doc (`_id` in filters) |
| `upsert` | false | Create if missing (requires `_id`/`id`, `update_many` false) |

`update_data` may use operators: `$set`, `$inc`, `$unset`, etc.

**200** — `{ "success", "modified_count", "matched_count", "upserted_id?" }`

**Safety:** non-empty `filters`; dangerous operators rejected; unknown DB/collection → **403**.

#### Delete — DELETE

```json
{
  "database_id": "<24_hex>",
  "collection_name": "users",
  "filters": { "_id": "<24_hex>" },
  "soft_delete": true
}
```

`soft_delete: false` permanently removes matches.

### 8.4 Files (GridFS)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/files/` | Paginated list |
| POST | `/api/v2/files/` | Multipart: `file`, optional `filename`, `content_type` |
| GET | `/api/v2/files/<file_id>/` | Metadata |
| DELETE | `/api/v2/files/<file_id>/` | Delete |
| GET | `/api/v2/files/stream/<file_id>/` | Stream body |
| GET | `/api/v2/files/download/<file_id>/` | Download |

`file_id` is 24 hex chars. Stream/download may require signed URL query parameters from list/detail responses.

---

## 9. Analytics API (`/analytics/api/v2/`)

**JWT only** — not available with API keys. Used by the dashboard SPA.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `dashboard/` | Overview metrics |
| GET | `performance/` | Latency percentiles, throughput |
| GET | `errors/` | Error breakdown |
| GET | `top-collections/` | Hot collections |
| GET | `slow-queries/` | Slow query log |
| GET | `endpoint-volume/` | Traffic by path |
| GET | `operation-breakdown/` | Operation mix |
| GET | `storage-trend/` | Storage over time |

Responses: `{ "success": true, … }` plus domain keys (`overview`, `percentiles_ms`, etc.).

---

## 10. Roles & permissions

| Role | Data API | Admin routes |
|------|----------|--------------|
| **developer** | Read + write (default) | No |
| **analyst** | Read-only on CRUD/files/lists | No |
| **admin** | Read + write | `prune_fields`, set user role |

Hide destructive UI actions for analysts. API keys inherit the user's role.

---

## 11. Errors & rate limits

| Status | Typical cause |
|--------|----------------|
| 400 | Validation / malformed JSON |
| 401 | Missing or invalid auth |
| 403 | Role, unverified email, quota, unknown resource |
| 404 | Not found |
| 429 | Auth endpoint throttling — exponential backoff |

Error bodies may be `{ "error": "…" }`, `{ "detail": "…" }`, or DRF field errors `{ "email": ["…"] }`.

---

## 12. Frontend application

**Path:** `UI/datacube-UI/`

| Feature | Route |
|---------|-------|
| Landing | `/` |
| API reference (developers) | `/api-docs` |
| Login / register / OTP / OAuth | `/login`, `/register`, `/oauth/callback`, … |
| Dashboard | `/dashboard/overview` |
| Profile | `/dashboard/profile` |
| API keys | `/dashboard/api-keys` |
| Database detail & documents | `/dashboard/database/:dbId`, `…/collection/:collName` |
| Files | `/dashboard/files/:fileId` |

**Env:** `VITE_API_BASE` — API origin (default `http://127.0.0.1:8000`).

**Stack:** React 19, React Router, TanStack Query, Zustand, Tailwind CSS v4, Framer Motion.

Run locally:

```bash
cd UI/datacube-UI
npm install
npm run dev
```

---

## 13. Local development & testing

### Backend

```bash
cd backend
uv sync
export SECRET_KEY=dev-insecure-key
export MONGODB_URI=mongodb://localhost:27017
export MONGODB_DATABASE=datacube_meta
export MONGODB_COLLECTION=databases
export AUTH_DB_NAME=datacube_auth
export FILE_STORAGE_DB_NAME=datacube_files
uv run python manage.py migrate
uv run python manage.py runserver
```

### Tests

```bash
cd backend
export SECRET_KEY=test MONGODB_URI=mongodb://localhost:27017 \
  MONGODB_DATABASE=test MONGODB_COLLECTION=meta AUTH_DB_NAME=auth FILE_STORAGE_DB_NAME=files
uv run pytest api/tests analytics/tests -q
```

API tests mock MongoDB and Celery — no live broker required.

### Frontend build

```bash
cd UI/datacube-UI
npm run build
```

---

## 14. Integration checklist

1. Store `access` + `refresh` securely; refresh on 401 (once) then re-login.
2. Send `Authorization: Bearer` or `Api-Key` on `/api/v2/*`.
3. Gate features on `email_verified` / `is_email_verified`.
4. Respect analyst read-only in clients.
5. Use `documents` in CRUD POST payloads.
6. Use non-empty `filters` on PUT/DELETE; include `_id` for single-doc updates.
7. Store API keys only at creation time.
8. For files, prefer signed URLs returned by the API when streaming/downloading.

---

## 15. Related source files

| Topic | Location |
|-------|----------|
| Data routes | `backend/api/presentation/urls_v2.py` |
| Auth routes | `backend/core/presentation/urls.py` |
| Data serializers | `backend/api/presentation/serializers.py` |
| Auth serializers | `backend/core/presentation/serializers.py` |
| JWT + API key | `backend/core/infrastructure/authentication.py` |
| User manager | `backend/core/infrastructure/managers.py` |
| Analytics routes | `backend/analytics/urls.py` |
| UI API reference data | `UI/datacube-UI/src/data/apiReference.ts` |
| SPA API guide | `backend/docs/FRONTEND_API_GUIDE.md` |

---

*Last updated with Datacube V2 profile, avatar DELETE, and developer-focused in-app API reference.*
