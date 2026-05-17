# Datacube V2

MongoDB-backed **database and document platform** with a Django REST API, JWT/API-key authentication, optional analytics, and a React dashboard UI.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | Django project: data plane (`api`), auth and billing (`core`), observability (`analytics`) |
| `UI/datacube-UI/` | React SPA for dashboards and account flows |
| `_frontend_old_nextjs/`, `_Datacube_api_libraries_old/` | Legacy snapshots (not part of the active architecture) |

## Backend: layered architecture

The Django apps stay named `api`, `core`, and `analytics` (migrations and `INSTALLED_APPS` unchanged). **Code inside each app is grouped by responsibility:**

### `api` (DataCube data plane)

| Layer | Package | Responsibility |
|-------|---------|----------------|
| **Presentation** | `api.presentation` | DRF serializers (`serializers.py`, `file_serializer.py`), URLconf (`urls_v2.py`), and HTTP views under `api.presentation.views` |
| **Application** | `api.application` | Orchestration services: metadata, databases, collections, documents, GridFS |
| **Infrastructure** | `api.infrastructure` | Mongo helpers, naming, signing URL helpers, validators |
| **Cross-cutting** | `api/` root | `middleware.py`, `permissions.py`, `models.py`, `admin.py`, `migrations/` |

Views inherit from `BaseAPIView` in `api.presentation.views.base`, which wires analytics hooks and shared error handling.

### `core` (accounts, JWT, API keys)

| Layer | Package |
|-------|---------|
| **Presentation** | `core.presentation` — `urls.py`, `serializers.py`, `views/` (auth, profile, API keys, Stripe webhooks) |
| **Infrastructure** | `core.infrastructure` — `authentication.py`, `db.py`, `managers.py` (Mongo user and auth DB access) |

DRF is configured to use `core.infrastructure.authentication.CustomJWTAuthentication` and `APIKeyAuthentication`.

**API reference for frontend teams:** [backend/docs/FRONTEND_API_GUIDE.md](backend/docs/FRONTEND_API_GUIDE.md).

### `analytics`

Task and middleware code for usage logging and dashboard APIs; URLs live in `analytics/urls.py` under the global prefix `analytics/api/v2/`.

## HTTP surface (prefixes)

These are mounted from `backend/project/urls.py`:

| Prefix | App | Examples |
|--------|-----|----------|
| `/api/v2/` | `api` | `create_database/`, `crud/`, `files/`, `health_check/` |
| `/core/` | `core` | `register/`, `login/`, `profile/`, `api/v1/keys/` |
| `/analytics/api/v2/` | `analytics` | `dashboard/`, `performance/`, … |
| `/admin/` | Django | Admin site |

Production host may differ; replace the host in examples with your deployment base URL.

### Health check

```bash
curl -sS "https://<host>/api/v2/health_check/"
```

Example JSON shape:

```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-05-15T12:00:00"
}
```

### Example: create a database (authenticated)

```bash
curl -X POST "https://<host>/api/v2/create_database/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "example_db",
    "collections": [
      {
        "name": "users",
        "fields": [
          {"name": "username", "type": "string"},
          {"name": "age", "type": "number"}
        ]
      }
    ]
  }'
```

### Allowed collection field types

`string`, `number`, `object`, `array`, `boolean`, `date`, `null`, `binary`, `objectid`, `decimal128`, `regex`, `timestamp`.

## Configuration (environment)

Required for `project.settings.common` (MongoDB and file storage):

- `MONGODB_URI`
- `MONGODB_DATABASE`
- `MONGODB_COLLECTION`
- `AUTH_DB_NAME`
- `FILE_STORAGE_DB_NAME`
- `SECRET_KEY` (set per environment; never commit real secrets)

Optional and feature-specific variables (Stripe, demo login, etc.) are read where those modules are used.

## Local development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
cd backend
uv sync
export SECRET_KEY=dev-insecure-key
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DATABASE=datacube_meta
export MONGODB_COLLECTION=databases
export AUTH_DB_NAME=datacube_auth
export FILE_STORAGE_DB_NAME=datacube_files
uv run python manage.py migrate
uv run python manage.py runserver
```

This creates `.venv/` from `uv.lock` (committed). Use `uv sync --no-dev` for a slimmer install without pytest or linters.

Use `project.settings.development` (default in `manage.py`) unless you override `DJANGO_SETTINGS_MODULE`.

## Tests

```bash
cd backend
export SECRET_KEY=test MONGODB_URI=mongodb://localhost:27017 \
  MONGODB_DATABASE=test MONGODB_COLLECTION=meta AUTH_DB_NAME=auth FILE_STORAGE_DB_NAME=files
uv run pytest api/tests analytics/tests -q
```

API tests mock MongoDB services and Celery `.delay` calls so they do not require Redis or a live broker.

## Documentation and API clients

- Primary API examples for `/api/v2/` are maintained in this README and in `backend/README.md`.
- Use JWT from `/core/login/` or API keys where enabled, then call `/api/v2/*` with `Authorization: Bearer <token>`.

## Contributing

Fork the repository, branch from the default line of development, run tests for touched apps, and open a pull request with a short note on behavior changes (especially URL or auth changes).

## License

See `backend/LICENSE` or the repository root license file if present.
