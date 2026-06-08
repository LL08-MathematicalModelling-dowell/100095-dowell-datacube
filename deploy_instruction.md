Here’s a practical recommendation for **your** app as it exists today.

## What the app implies today

| Path | Effective limit today | Notes |
|------|----------------------|--------|
| `POST /api/v2/files/` | **No app limit** | Only blocked by nginx default **1m** in prod |
| `GET .../files/download/` | **20 MB** | 413 above this; large files use `/stream/` |
| `POST /core/.../avatar/` | **3 MB** | Returns **400**, not 413 |
| `POST /api/v2/crud/...` | Up to **500 docs**/request | Large JSON bodies possible |
| Account storage | **500 MB** total (`DATACUBE_FREE_TIER_MB`) | Quota on CRUD writes, **not** on file upload yet |

So nginx at **1 MB** (default) is far too small. Uploads above ~1 MB fail at the proxy before Django.

---

## Recommended nginx values

Use **location-specific** limits instead of one global size:

```nginx
# Avatars only (3 MB app limit + multipart overhead)
location /core/ {
    client_max_body_size 5m;
    proxy_pass http://backend:8000;
    # ... existing proxy_set_header / timeouts ...
}

# GridFS uploads + large CRUD JSON batches
location /api/ {
    client_max_body_size 100m;
    proxy_pass http://backend:8000;
    proxy_read_timeout 300;      # optional: large uploads on slow links
    proxy_connect_timeout 90;
    # ... existing headers ...
}

# Analytics / auth JSON only — keep smaller
location /analytics/ {
    client_max_body_size 10m;
    proxy_pass http://backend:8000;
    # ...
}
```

### Why these numbers

- **`/api/` → `100m`**  
  - Above the **20 MB** download cutoff, so users can upload files they later fetch via **stream**.  
  - Room for fat CRUD batches (500 documents) without nginx rejecting the body.  
  - Still bounded (unlike `500m`, which would allow one request to equal the whole free-tier quota and is risky for DoS/memory).

- **`/core/` → `5m`**  
  - Matches avatar cap (3 MB) with headroom for multipart encoding.

- **`/analytics/` → `10m`**  
  - Query params + small JSON only; no file uploads.

If you want a **simpler** setup and only one knob:

```nginx
client_max_body_size 100m;   # inside the server { } block, or only on /api/
```

That fixes file uploads without opening `/core/` more than needed.

---

## What I would **not** use

| Value | Why |
|-------|-----|
| **1m** (nginx default) | Current effective limit; breaks almost any real file upload |
| **20m** only on `/api/` | Matches download buffer, but upload has no 20m cap — inconsistent UX |
| **500m** | Same as full free-tier quota in one POST; heavy on disk/RAM/timeouts |

---

## Align nginx with the app (recommended follow-up)

Nginx should be **≥** whatever you enforce in Django. Right now upload is unlimited in code, so pick a product max and mirror it:

| Layer | Suggested value |
|-------|-----------------|
| Nginx `/api/` | **`100m`** (or **`50m`** if you want stricter) |
| Django app check on `POST /files/` | **`100m`** or **`50m`** per file |
| Download in-memory endpoint | Keep **`20m`** (use stream above that) |
| Avatar | Keep **`3m`** |

Example product choice many teams use here: **50 MB per file upload**, **100m** nginx (buffer for multipart), **20 MB** download-in-memory, **stream** for larger downloads.

---

## Also check (not nginx, but related)

- **Gunicorn/uvicorn** — large uploads may need longer worker timeout than default.  
- **`proxy_read_timeout`** — you have **90s** on `/api/`; for 50–100 MB on slow networks, **300s** on `/api/` is reasonable.  
- **Enforce size in `FileListView.post`** — otherwise nginx is the only upload gate.

**Bottom line:** set **`client_max_body_size 100m`** on **`location /api/`**, **`5m`** on **`location /core/`**, and add a matching per-file limit in the backend when you’re ready. That matches GridFS uploads, the 20 MB download rule, and your 500 MB account quota without allowing a single 500 MB upload by default.




Here’s the deployment setup added for **build on GitHub → pull on VPS**.

## What happens on each push to `main`

1. **Build & push** `datacube-backend` and `datacube-frontend` to GHCR  
   - Tags: `latest` and `<commit-sha>`
2. **SCP** only `deploy/docker-compose.yml` to your VPS (`WORKING_DIR`)
3. **SSH** on the VPS: `docker login` → `compose pull` → `compose up -d`

No git pull or `docker build` on the server.

## New / updated files

| Path | Role |
|------|------|
| [`deploy/docker-compose.yml`](deploy/docker-compose.yml) | Image-only stack (no `build:`) |
| [`deploy/.env.example`](deploy/.env.example) | Image names + tag (on VPS) |
| [`deploy/config/backend.env.example`](deploy/config/backend.env.example) | Django secrets template (on VPS) |
| [`deploy/README.md`](deploy/README.md) | Full setup guide |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | Build, push, SCP, deploy |
| [`UI/datacube-UI/Dockerfile`](UI/datacube-UI/Dockerfile) | `VITE_*` build args for CI |

## What you need to configure

### On the VPS (once)

```bash
mkdir -p /opt/datacube/config
cd /opt/datacube
# copy examples from the repo (or create manually):
#   .env  ← BACKEND_IMAGE, FRONTEND_IMAGE (ghcr.io/<user>/datacube-backend)
#   config/backend.env  ← MongoDB, SECRET_KEY, etc.
docker network create app-network
```

Keep **host nginx + TLS** as today (`nginx/nginx.prod.conf`); compose only runs `redis`, `backend`, `celery`, `react-app`, `autoheal`.

### GitHub → Settings → Secrets

| Secret | Example |
|--------|---------|
| `SSH_HOST` | VPS IP or hostname |
| `SSH_PORT` | `22` |
| `USER_NAME` | `deploy` |
| `SSH_PRIVATE_KEY` | PEM private key |
| `WORKING_DIR` | `/opt/datacube` |
| `GHCR_PULL_TOKEN` | PAT with **`read:packages`** |

### GitHub → Settings → Variables

| Variable | Example |
|----------|---------|
| `VITE_API_BASE` | `https://datacube.uxlivinglab.online` |

Optional secrets for OAuth in the frontend build: `VITE_GITHUB_OAUTH_CLIENT_ID`, etc.

### GHCR

After the first workflow run, open **Packages** on GitHub and ensure the VPS user/PAT can pull (private packages need `GHCR_PULL_TOKEN`).

---

**Note:** `config/backend.env` and `.env` stay on the VPS only; Actions does not overwrite them—only `docker-compose.yml` is copied each deploy. `IMAGE_TAG` is set to the commit SHA during deploy.

I can commit this in a grouped style if you want, or adjust image names / add a staging workflow.
