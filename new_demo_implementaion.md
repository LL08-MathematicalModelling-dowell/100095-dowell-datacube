**Why it’s probably broken again**

The current setup has a few weak points stacked together:

1. **Static HTML outside the app** — `Playground/demo-playground.html` must be manually mounted on host nginx (`/usr/share/nginx/html/demo/`). Your `deploy/docker-compose.yml` has no nginx service, so `/demo/` often 404s after redeploys.
2. **Shared demo account** — Everyone logs into **one** user (`DEMO_LOGIN_EMAIL`, default `samanta@dowellresearch.se`). If that user doesn’t exist or isn’t verified in prod → `404` / `403`.
3. **`DEMO_AUTO_ENSURE_USER` likely off in prod** — Without it, the backend won’t auto-create the demo user.
4. **`DEMO_PLAYGROUND_SECRET` isn’t used** — Defined in settings but never checked; no real protection on the endpoint.

So it’s fragile on **deployment** and **data** (one shared sandbox everyone can trash).

---

**What I’d recommend instead**

### Best approach: **ephemeral playground sessions** (one temp user per visitor)

On “Try Datacube”:

1. Backend creates a **new short-lived user**, e.g. `playground-<uuid>@demo.datacube.internal`
2. Marks it `is_playground: true`
3. **Clones a seed template** (sample DB + collections + a few docs)
4. Returns JWTs like today
5. **Celery job** deletes playground users + their data after **2–4 hours** (or nightly sweep)

**Limits for playground users** (enforced in middleware or service layer):

| Limit | Example |
|--------|---------|
| Max databases | 1 |
| Max collections | 3 |
| Max documents | 100 |
| File uploads | Off or tiny (e.g. 1 MB) |
| API keys / admin | Disabled |
| Rate limit | Stricter than normal |

**Why this is better**

- Each visitor gets a **fresh sandbox** — no shared mess
- No need to “rotate” one account — **TTL + cleanup** handles it
- Fits your existing model (everything is `user_id`-scoped)
- Safer than a public passwordless login to a real account

---

### Quick win (do first): **move demo into the React app**

- Add route `/demo` or `/try` in the SPA (no separate static file / nginx mount)
- “Launch demo” → `POST /core/api/v2/demo/login/`
- Serve from the same frontend image you already deploy

Fixes hosting; **doesn’t** fix shared-account pollution.

---

### Alternatives (I’d avoid as primary)

| Approach | Issue |
|----------|--------|
| **One shared account + nightly reset** | Visitors still overwrite each other all day |
| **Rotating shared accounts** | Ops overhead, still shared within rotation window |
| **Read-only demo only** | Fine for a tour, but not a real “playground” |

---

**Practical rollout**

1. **Now:** `/try` in React + prod env: `DEMO_AUTO_ENSURE_USER=1`, verified demo user (or ephemeral MVP)
2. **Next:** Ephemeral users + seed template + TTL cleanup
3. **Optional:** Require `DEMO_PLAYGROUND_SECRET` header, or CAPTCHA, if abuse shows up

---

**Bottom line**

Keep the one-click idea, but stop using **one permanent shared account**. **Ephemeral playground users with limits and auto-cleanup** is the right long-term model for Datacube.

If you want to implement, I’d start with **React `/try` route** (fixes deployment) then **ephemeral sessions** (fixes the product). Say which phase you want first.