# Datacube V2

MongoDB-backed **database and document platform** with a Django REST API, JWT/API-key authentication, analytics dashboards, and a React operator UI.

## Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| **[datacube_documentation.md](datacube_documentation.md)** | Everyone | Full platform reference — architecture, all APIs, roles, setup |
| **[backend/docs/FRONTEND_API_GUIDE.md](backend/docs/FRONTEND_API_GUIDE.md)** | SPA authors | Auth flows, profile, CRUD semantics for the dashboard |
| **In-app `/api-docs`** | Integrators | Curated developer APIs with cURL, Python, TypeScript, and JavaScript samples |

Start with **datacube_documentation.md** for the complete picture; use the UI API reference when building integrations.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | Django project: data plane (`api`), auth (`core`), observability (`analytics`) |
| `UI/datacube-UI/` | React SPA — dashboards, account, developer API reference |
| `datacube_documentation.md` | Canonical full API & project documentation |
| `_frontend_old_nextjs/`, `_Datacube_api_libraries_old/` | Legacy snapshots (not part of active architecture) |

## Backend: layered architecture

The Django apps stay named `api`, `core`, and `analytics` (migrations and `INSTALLED_APPS` unchanged). **Code inside each app is grouped by responsibility:**

### `api` (DataCube data plane)

| Layer | Package | Responsibility |
|-------|---------|----------------|
| **Presentation** | `api.presentation` | DRF serializers, `urls_v2.py`, HTTP views |
| **Application** | `api.application` | Metadata, databases, collections, documents, GridFS |
| **Infrastructure** | `api.infrastructure` | Mongo helpers, naming, signing URL helpers, validators |
| **Cross-cutting** | `api/` root | `middleware.py`, `permissions.py`, `models.py` |

Views inherit from `BaseAPIView` in `api.presentation.views.base`, which wires analytics hooks and shared error handling.

### `core` (accounts, JWT, API keys)

| Layer | Package |
|-------|---------|
| **Presentation** | `core.presentation` — `urls.py`, serializers, views (auth, profile, API keys) |
| **Infrastructure** | `core.infrastructure` — `authentication.py`, `managers.py` (Mongo user and auth DB) |

DRF uses `core.infrastructure.authentication.CustomJWTAuthentication` and `APIKeyAuthentication`.

### `analytics`

Task and middleware code for usage logging and dashboard APIs; URLs in `analytics/urls.py` under `analytics/api/v2/`.

## HTTP surface (prefixes)

Mounted from `backend/project/urls.py`:

| Prefix | App | Examples |
|--------|-----|----------|
| `/api/v2/` | `api` | `create_database/`, `crud/`, `files/`, `health_check/` |
| `/core/` | `core` | `login/`, `profile/`, `api/v1/keys/` |
| `/analytics/api/v2/` | `analytics` | `dashboard/`, `performance/`, … |
| `/admin/` | Django | Admin site |

See [datacube_documentation.md §5–9](datacube_documentation.md#5-http-surface) for every endpoint.

### Quick example: health check

```bash
curl -sS "https://<host>/api/v2/health_check/"
```

### Quick example: create a database (authenticated)

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

Optional variables (Stripe, OAuth, demo login, email) are documented in [datacube_documentation.md §4](datacube_documentation.md#4-configuration) and `backend/.env.example`.

## Local development

### Backend

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

Use `project.settings.development` (default in `manage.py`) unless you override `DJANGO_SETTINGS_MODULE`.

### Frontend

```bash
cd UI/datacube-UI
npm install
npm run dev
```

Set `VITE_API_BASE` if the API is not on `http://127.0.0.1:8000`. Open `/api-docs` for the developer API reference with multi-language samples.

## Tests

```bash
cd backend
export SECRET_KEY=test MONGODB_URI=mongodb://localhost:27017 \
  MONGODB_DATABASE=test MONGODB_COLLECTION=meta AUTH_DB_NAME=auth FILE_STORAGE_DB_NAME=files
uv run pytest api/tests analytics/tests -q
```

API tests mock MongoDB services and Celery `.delay` calls — no Redis or live broker required.

## Production deployment (GitHub Actions → VPS)

Images are built in CI and pushed to **GitHub Container Registry (GHCR)**. The VPS only receives `deploy/docker-compose.yml` and runs `docker compose pull` / `up` — no git clone or on-server builds.

See **[deploy/README.md](deploy/README.md)** for one-time VPS setup, GitHub secrets (`SSH_*`, `GHCR_PULL_TOKEN`, `WORKING_DIR`), and variables (`VITE_API_BASE`).

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, commit style, tests, and pull request expectations.

## License

See `backend/LICENSE` or the repository root license file if present.
