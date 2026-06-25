# Contributing to Datacube V2

Thank you for helping improve Datacube. This guide explains how to set up the project, what we expect in pull requests, and how releases reach production.

## Before you start

- Read [README.md](README.md) for the repository layout and quick start.
- Use [datacube_documentation.md](datacube_documentation.md) as the canonical reference for APIs, configuration, and roles.

## Development setup

Common shortcuts via **Makefile** at the repo root (`make help`):

```bash
make setup          # first time: .env, uv sync, migrate, npm install
make dev-backend    # Django on :8000
make dev-ui         # Vite on :5173 (separate terminal)
make docker-up      # full stack in Docker
make test           # backend pytest
```

### Backend (Python 3.11, [uv](https://docs.astral.sh/uv/))

```bash
cd backend
uv sync
cp .env.example .env   # then edit with local MongoDB and secrets
export SECRET_KEY=dev-insecure-key
export MONGODB_URI=mongodb://127.0.0.1:27017
export MONGODB_DATABASE=datacube_meta
export MONGODB_COLLECTION=databases
export AUTH_DB_NAME=datacube_auth
export FILE_STORAGE_DB_NAME=datacube_files
uv run python manage.py migrate
uv run python manage.py runserver
```

`manage.py` defaults to `project.settings.development`. See [backend/README.md](backend/README.md) for Docker-based dev (`Dockerfile.dev` + `docker-compose.dev_enhanced.yml`).

**Dependencies:** edit `pyproject.toml`, then run `uv lock` and commit the updated `uv.lock`. Do not add `requirements.txt`.

### Frontend (React + Vite)

```bash
cd UI/datacube-UI
npm install
npm run dev
```

Set `VITE_API_BASE` when the API is not at `http://127.0.0.1:8000`. OAuth and other `VITE_*` variables are documented in [datacube_documentation.md §4](datacube_documentation.md#4-configuration).

### Full stack with Docker

```bash
docker compose -f docker-compose.dev_enhanced.yml up --build
```

Backend and Celery images use `uv sync` inside `backend/Dockerfile.dev`.

## Project structure (where to put changes)

| Area | Path | Notes |
|------|------|--------|
| Data API (CRUD, files, metadata) | `backend/api/` | Presentation → application → infrastructure |
| Auth, profile, API keys | `backend/core/` | JWT and API-key authentication |
| Analytics | `backend/analytics/` | Dashboard APIs and telemetry tasks |
| Dashboard UI | `UI/datacube-UI/src/` | React SPA |
| Platform docs | `datacube_documentation.md`, `README.md` | Update when behavior or URLs change |
| Deploy | `deploy/` | VPS compose + examples only; secrets stay on the server |

New API views should inherit from `BaseAPIView` in `api.presentation.views.base` so analytics and error handling stay consistent.

## Branching and pull requests

1. Fork the repository (or create a branch on the main repo if you have write access).
2. Branch from `main` with a short, descriptive name (e.g. `feat/inventory-date-filter`, `fix/oauth-callback`).
3. Keep changes focused — one logical feature or fix per PR when possible.
4. Run the checks below before opening the PR.
5. Open a pull request against `main` and describe:
   - **What** changed and **why**
   - Any **API**, auth, or URL changes (call these out explicitly)
   - How you tested (commands or manual steps)

We do not require a issue link for every PR, but reference one if it exists.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) with a scope that matches the area of the codebase:

```
<type>(<scope>): <short description>
```

| Type | Use for |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Tooling, deps, cleanup |
| `refactor` | Code change without behavior change |

**Scopes** we commonly use: `api`, `core`, `analytics`, `ui`, `docs`, `deploy`.

Examples from this repository:

- `feat(core): extend profile API with has_avatar and avatar DELETE`
- `fix(ui): dedupe OAuth callback exchange under React Strict Mode`
- `docs: add full platform documentation and refresh README`

Prefer several small, scoped commits over one large mixed commit.

## Tests and CI

### Backend (required for `backend/` changes)

CI runs on pull requests that touch `backend/**` (see [.github/workflows/ci.yml](.github/workflows/ci.yml)):

```bash
cd backend
export SECRET_KEY=test
export MONGODB_URI=mongodb://127.0.0.1:27017
export MONGODB_DATABASE=datacube_ci
export MONGODB_COLLECTION=metadata
export AUTH_DB_NAME=datacube_auth_ci
export FILE_STORAGE_DB_NAME=datacube_files_ci
uv sync --frozen --all-groups
uv run pytest
uv run python manage.py check
```

Tests mock MongoDB and Celery `.delay` — you do not need Redis or a live broker for unit tests.

Add or update tests when you change behavior in `api/`, `core/`, or `analytics/`. Skip tests that only assert obvious framework behavior.

### Frontend

There is no automated UI test job in CI yet. For UI changes, run locally:

```bash
cd UI/datacube-UI
npm run build
```

Fix TypeScript and build errors before requesting review.

## Code guidelines

- **Match existing style** in the file you edit (naming, async views, serializer patterns).
- **Minimize scope** — avoid drive-by refactors or unrelated formatting.
- **Security** — never commit `.env`, `.env.prod`, `backend.env`, API keys, or real `SECRET_KEY` values. Use `backend/.env.example` and `deploy/config/backend.env.example` as templates only.
- **User scoping** — data access must stay tied to the authenticated user (metadata and GridFS paths are user-scoped).
- **Roles** — respect `developer` / `analyst` / `admin`; analysts must not get destructive write paths.
- **Comments** — only where logic is non-obvious; prefer clear code over long comments.

## Documentation

Update docs when you change:

- HTTP routes or request/response shapes → `datacube_documentation.md` and, if relevant, in-app `/api-docs` content
- Environment variables → `backend/.env.example` and documentation §4
- Deployment or Docker → `deploy/README.md`, `README.md`, or `backend/README.md`

## Deployment (maintainers)

Pushes to `main` trigger [.github/workflows/deploy.yml](.github/workflows/deploy.yml): build images with `backend/Dockerfile.prod`, push to GHCR, copy `deploy/docker-compose.yml` to the VPS, and `docker compose pull` / `up`.

Contributors do not need VPS access; maintainers handle GitHub secrets and production config per [deploy/README.md](deploy/README.md).

## Questions

If something in this guide is unclear or out of date, open an issue or note it in your PR so we can update `CONTRIBUTING.md`.

## License

By contributing, you agree that your contributions are licensed under the same terms as the project — see [LICENSE](LICENSE).
