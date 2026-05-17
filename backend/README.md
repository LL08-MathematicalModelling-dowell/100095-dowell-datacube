# Datacube V2 — Django backend

Django 5.x + Django REST Framework + `adrf` async views, MongoDB for metadata and documents, SQLite for Django’s own tables unless overridden.

## Architecture (inside `api` and `core`)

- **`api.presentation`** — Serializers, `urls_v2.py`, `views/` (CRUD, files, admin-style list/drop/import, health).
- **`api.application`** — `MetadataService`, `DatabaseService`, `CollectionService`, `DocumentService`, `GridFSService`.
- **`api.infrastructure`** — `mongodb.py`, `validators.py`, `naming.py`, `signing.py`.

- **`core.presentation`** — Account and dashboard HTTP API: `urls.py`, `serializers.py`, `views/`.
- **`core.infrastructure`** — `authentication.py`, `db.py`, `managers.py`.

The `analytics` app keeps its own layout (tasks, middleware, `views/analytics_views.py`).

## URL entrypoints

| Django include | Module |
|----------------|--------|
| `api/v2/` | `api.presentation.urls_v2` |
| `core/` | `core.presentation.urls` |
| `analytics/api/v2/` | `analytics.urls` |

### Frontend / mobile API guide

See **[docs/FRONTEND_API_GUIDE.md](docs/FRONTEND_API_GUIDE.md)** for base URLs, authentication (JWT, API keys, OAuth, OTP), routes, roles, and example payloads.

## Public data API (`/api/v2/`)

Endpoints include (all typically authenticated except `health_check`):

- `POST/GET …/create_database/`, `add_collection/`
- `GET …/list_databases/`, `list_collections/`, `get_metadata/`
- `DELETE …/drop_database/`, `drop_collections/`
- `POST …/import_data/`
- `POST/GET/PUT/DELETE …/crud/`
- `…/files/` — list/upload; `files/<id>/`, `files/stream/<id>/`, `files/download/<id>/`
- `GET …/health_check/`
- `POST …/admin/prune_fields/` — admin permission; prunes inactive field metadata (`database_id`, optional `dry_run`)

Trailing slashes are optional on these routes (see `re_path` patterns in `api/presentation/urls_v2.py`).

## Auth API (`/core/`)

Registration, login, refresh, email verification, password reset, profile, API keys (`api/v1/keys/`), and related routes are declared in `core/presentation/urls.py`.

## Quick cURL examples

Replace `<HOST>` and tokens with your values.

```bash
# Health (no auth)
curl -sS "https://<HOST>/api/v2/health_check/"

# CRUD create (JWT) — body field is `documents`, not `data`
curl -X POST "https://<HOST>/api/v2/crud/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"database_id":"<DB_ID>","collection_name":"users","documents":[{"username":"alice"}]}'
```

## Dependencies (uv)

This project uses **[uv](https://docs.astral.sh/uv/)** (`pyproject.toml` + `uv.lock`). Python **3.11** is pinned via `.python-version`.

```bash
# Install uv: https://docs.astral.sh/uv/getting-started/installation/
cd backend
uv sync              # runtime + dev dependencies (creates .venv/)
uv sync --no-dev     # production-only (e.g. CI mimicking the image)
```

Run commands inside the environment with `uv run` (or activate `.venv` manually):

```bash
uv run python manage.py migrate
uv run python manage.py runserver
uv run pytest api/tests analytics/tests -q
```

Docker production builds use `uv sync --frozen --no-dev` in `Dockerfile.prod` (no `requirements.txt`).

## Running locally

Install dependencies with `uv sync`, set the same environment variables as in the root README, then:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

See the root [README.md](../README.md) for the full variable list.

## Tests

`pytest.ini` sets `DJANGO_SETTINGS_MODULE` and `asyncio_mode`. Example:

```bash
export SECRET_KEY=test MONGODB_URI=mongodb://127.0.0.1:27017 \
  MONGODB_DATABASE=test MONGODB_COLLECTION=meta AUTH_DB_NAME=auth FILE_STORAGE_DB_NAME=files
uv run pytest api/tests analytics/tests -q
```
