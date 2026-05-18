/**
 * API reference content aligned with backend `docs/FRONTEND_API_GUIDE.md`.
 * Paths use trailing slashes where the Django routes support them (optional slash also works).
 */

export interface ApiMethod {
  method: string;
  body?: string;
  params?: string;
  response: string;
}

export interface ApiEndpoint {
  name: string;
  description?: string;
  /** e.g. "JWT", "None (public)", "JWT or Api-Key" */
  auth_required?: string;
  url: string;
  methods: ApiMethod[];
  notes?: string;
}

export interface ApiGroup {
  group: string;
  description: string;
  auth_header?: string;
  how_to_get_key?: string;
  endpoints: ApiEndpoint[];
}

const j = (o: unknown) => JSON.stringify(o, null, 2);

export const apiDocs: ApiGroup[] = [
  {
    group: "Auth & account (`/core/`)",
    description:
      "Registration, login, JWT refresh, profile, API keys, OAuth (PKCE), OTP, and password reset. Send JSON unless noted. Requires verified email for token-gated usage.",
    auth_header: "Authorization: Bearer <access_token>",
    how_to_get_key:
      "Login or complete OTP/OAuth to receive `access` and `refresh`. For automation after login, create an API key via POST /core/api/v1/keys/ and use Authorization: Api-Key <key>.",
    endpoints: [
      {
        name: "Register",
        auth_required: "None",
        description:
          "Create account; OTP sent for email verification. Stripe customer may be created server-side.",
        url: "/core/register/",
        methods: [
          {
            method: "POST",
            body: j({
              email: "user@example.com",
              firstName: "Ada",
              lastName: "Lovelace",
              password: "minimum8chars",
            }),
            response: j({ message: "Check your email for verification code." }),
          },
        ],
      },
      {
        name: "Login",
        auth_required: "None",
        description:
          "Password login. 403 `email_unverified` until OTP completed. 401 invalid credentials.",
        url: "/core/login/",
        methods: [
          {
            method: "POST",
            body: j({ email: "user@example.com", password: "…" }),
            response: j({
              access: "…",
              refresh: "…",
              firstName: "Ada",
              lastName: "Lovelace",
              role: "developer",
              email_verified: true,
            }),
          },
        ],
      },
      {
        name: "Refresh access token",
        auth_required: "Refresh token in body",
        description: "Exchange refresh for a new access token.",
        url: "/core/auth/token/refresh/",
        methods: [
          {
            method: "POST",
            body: j({ refresh: "<refresh_token>" }),
            response: j({ access: "<new_access_token>" }),
          },
        ],
      },
      {
        name: "Profile",
        auth_required: "JWT",
        description: "Read or update name fields for the current user.",
        url: "/core/profile/",
        methods: [
          {
            method: "GET",
            response: j({
              id: "…",
              email: "user@example.com",
              firstName: "Ada",
              role: "developer",
              is_email_verified: true,
            }),
          },
          {
            method: "PATCH",
            body: j({ firstName: "Ada", lastName: "L." }),
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "API keys",
        auth_required: "JWT only",
        description:
          "List metadata (no full secret). POST returns `key` once — store it. DELETE revokes by Mongo id.",
        url: "/core/api/v1/keys/",
        methods: [
          {
            method: "GET",
            response: j([
              {
                _id: "…",
                name: "My integration",
                key_display: "sk_test_****…",
                created_at: "2026-01-01T00:00:00Z",
                is_active: true,
              },
            ]),
          },
          {
            method: "POST",
            body: j({ name: "My integration" }),
            response: j({
              key: "sk_test_…",
              name: "My integration",
              id: "…",
              created_on: "…",
            }),
          },
        ],
        notes: "DELETE /core/api/v1/keys/<key_id>/ — revoke key.",
      },
      {
        name: "Request OTP",
        auth_required: "None",
        description:
          "purpose: `register` | `login_email`. Response is intentionally vague (anti-enumeration).",
        url: "/core/auth/otp/request/",
        methods: [
          {
            method: "POST",
            body: j({ email: "user@example.com", purpose: "register" }),
            response: j({
              message: "If an account matches, a code was sent.",
            }),
          },
        ],
      },
      {
        name: "Verify OTP → JWT",
        auth_required: "None",
        description: "Same response shape as password login on success.",
        url: "/core/auth/otp/verify/",
        methods: [
          {
            method: "POST",
            body: j({
              email: "user@example.com",
              code: "123456",
              purpose: "register",
            }),
            response: j({
              access: "…",
              refresh: "…",
              firstName: "Ada",
              role: "developer",
              email_verified: true,
            }),
          },
        ],
      },
      {
        name: "OAuth (Google / GitHub PKCE)",
        auth_required: "None",
        description:
          "Server exchanges authorization `code` (not client ID token). 503 if OAuth not configured.",
        url: "/core/auth/oauth/google/",
        methods: [
          {
            method: "POST",
            body: j({
              code: "<from provider redirect>",
              code_verifier: "<PKCE verifier>",
              redirect_uri: "https://your-app.example/oauth/callback",
            }),
            response: j({ access: "…", refresh: "…", firstName: "…" }),
          },
        ],
        notes: "GitHub: POST /core/auth/oauth/github/ with the same JSON shape.",
      },
      {
        name: "Password reset",
        auth_required: "None",
        description: "Request OTP to email, then confirm with new password (min 8 chars).",
        url: "/core/password-reset/request/",
        methods: [
          {
            method: "POST",
            body: j({ email: "user@example.com" }),
            response: j({ message: "…" }),
          },
        ],
        notes: "Confirm: POST /core/password-reset/confirm/ with email, code, password.",
      },
      {
        name: "Demo login",
        auth_required: "None (non-prod only)",
        description:
          "If enabled on the server, returns JWTs without a password for a fixed demo user.",
        url: "/core/api/v2/demo/login/",
        methods: [
          {
            method: "POST",
            response: j({ access: "…", refresh: "…" }),
          },
        ],
      },
    ],
  },
  {
    group: "Data API (`/api/v2/`)",
    description:
      "Databases, collections, CRUD, and GridFS files. Default authenticated; roles apply (analyst is read-only on mutating routes). Use `documents` (not `data`) in CRUD insert payloads.",
    auth_header: "Authorization: Bearer <access_token>",
    how_to_get_key:
      "Alternatively: Authorization: Api-Key <sk_test_…> (same role rules as JWT; email must be verified).",
    endpoints: [
      {
        name: "Health",
        auth_required: "None (public)",
        description: "Liveness check.",
        url: "/api/v2/health_check/",
        methods: [
          {
            method: "GET",
            response: j({ status: "ok" }),
          },
        ],
      },
      {
        name: "Create database",
        auth_required: "JWT — developer or admin",
        description: "Logical database + initial collections and field hints.",
        url: "/api/v2/create_database/",
        methods: [
          {
            method: "POST",
            body: j({
              db_name: "my_app",
              collections: [
                {
                  name: "users",
                  fields: [{ name: "email", type: "string" }],
                },
              ],
            }),
            response: j({
              success: true,
              database: { id: "<24_hex>", name: "my_app" },
              collections: ["users"],
            }),
          },
        ],
      },
      {
        name: "List databases",
        auth_required: "JWT",
        description: "Paginated list; optional search.",
        url: "/api/v2/list_databases/",
        methods: [
          {
            method: "GET",
            params: "page=1&page_size=50&search=",
            response: j({
              success: true,
              data: [],
              pagination: {
                page: 1,
                page_size: 50,
                total_items: 0,
                total_pages: 0,
              },
            }),
          },
        ],
      },
      {
        name: "List collections",
        auth_required: "JWT",
        url: "/api/v2/list_collections/",
        description: "Collections for one database.",
        methods: [
          {
            method: "GET",
            params: "database_id=<24_hex>",
            response: j({ success: true, data: [] }),
          },
        ],
      },
      {
        name: "Get metadata",
        auth_required: "JWT",
        url: "/api/v2/get_metadata/",
        description: "Full metadata document for a database.",
        methods: [
          {
            method: "GET",
            params: "database_id=<24_hex>",
            response: j({ success: true, data: {} }),
          },
        ],
      },
      {
        name: "Add collections",
        auth_required: "JWT — developer or admin",
        url: "/api/v2/add_collection/",
        methods: [
          {
            method: "POST",
            body: j({
              database_id: "<24_hex>",
              collections: [
                { name: "orders", fields: [{ name: "total", type: "number" }] },
              ],
            }),
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "Drop database",
        auth_required: "JWT — developer or admin",
        url: "/api/v2/drop_database/",
        methods: [
          {
            method: "DELETE",
            body: j({
              database_id: "<24_hex>",
              confirmation: "<must match displayName>",
            }),
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "Drop collections",
        auth_required: "JWT — developer or admin",
        url: "/api/v2/drop_collections/",
        methods: [
          {
            method: "DELETE",
            body: j({
              database_id: "<24_hex>",
              collection_names: ["coll_a"],
            }),
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "CRUD",
        auth_required: "JWT — analyst: GET only",
        description:
          "Single endpoint for insert/query/update/delete. Query uses filters as JSON string. ObjectIds are 24-char hex.",
        url: "/api/v2/crud/",
        methods: [
          {
            method: "POST",
            body: j({
              database_id: "<24_hex>",
              collection_name: "users",
              documents: [{ username: "alice" }],
            }),
            response: j({ success: true, inserted_ids: ["…"] }),
          },
          {
            method: "GET",
            params:
              "database_id=<24_hex>&collection_name=users&filters={}&page=1&page_size=50",
            response: j({
              success: true,
              data: [],
              pagination: {},
            }),
          },
          {
            method: "PUT",
            body: j({
              database_id: "<24_hex>",
              collection_name: "users",
              filters: { _id: "<24_hex>" },
              update_data: { status: "active" },
              update_all_fields: true,
              update_many: false,
              upsert: false,
            }),
            response: j({
              success: true,
              modified_count: 1,
              matched_count: 1,
            }),
          },
          {
            method: "DELETE",
            body: j({
              database_id: "<24_hex>",
              collection_name: "users",
              filters: { status: "archived" },
              soft_delete: true,
            }),
            response: j({ success: true, count: 1 }),
          },
        ],
        notes:
          "POST: max 500 documents. PUT/DELETE: filters required; single update needs _id. update_all_fields=true allows new fields; false patches existing fields only. upsert with _id creates if missing. soft_delete true (default) sets is_deleted.",
      },
      {
        name: "Files (GridFS)",
        auth_required: "JWT",
        description: "Upload, list, metadata, stream, download.",
        url: "/api/v2/files/",
        methods: [
          {
            method: "GET",
            params: "page=1&page_size=50&search=",
            response: j({ success: true, data: [] }),
          },
          {
            method: "POST",
            body: "multipart/form-data: fields `file`, optional `filename`, `content_type`",
            response: j({ success: true, file_id: "<24_hex>" }),
          },
        ],
        notes:
          "GET /api/v2/files/<file_id>/ — metadata. DELETE same path. GET /api/v2/files/stream/<file_id>/ and /download/<file_id>/ — streaming; may require signed URL query params when returned by API.",
      },
      {
        name: "Import JSON",
        auth_required: "JWT — developer or admin",
        url: "/api/v2/import_data/",
        methods: [
          {
            method: "POST",
            body: "multipart: json_file + database_id + optional collection_name",
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "Prune field metadata (admin)",
        auth_required: "JWT — admin",
        url: "/api/v2/admin/prune_fields/",
        methods: [
          {
            method: "POST",
            body: j({ database_id: "<24_hex>", dry_run: true }),
            response: j({ success: true, result: {} }),
          },
        ],
      },
    ],
  },
  {
    group: "Analytics (`/analytics/api/v2/`)",
    description:
      "Operational metrics for dashboards. All routes require JWT. Responses include success: true plus domain payloads (overview, percentiles_ms, etc.).",
    auth_header: "Authorization: Bearer <access_token>",
    how_to_get_key: "API keys are not used here — use JWT from login.",
    endpoints: [
      {
        name: "Dashboard overview",
        auth_required: "JWT",
        url: "/analytics/api/v2/dashboard/",
        methods: [
          {
            method: "GET",
            response: j({ success: true, overview: {} }),
          },
        ],
      },
      {
        name: "Performance",
        auth_required: "JWT",
        url: "/analytics/api/v2/performance/",
        methods: [
          {
            method: "GET",
            response: j({ success: true, percentiles_ms: {}, throughput: [] }),
          },
        ],
      },
      {
        name: "Errors",
        auth_required: "JWT",
        url: "/analytics/api/v2/errors/",
        methods: [{ method: "GET", response: j({ success: true }) }],
      },
      {
        name: "Top collections",
        auth_required: "JWT",
        url: "/analytics/api/v2/top-collections/",
        methods: [{ method: "GET", response: j({ success: true }) }],
      },
      {
        name: "Slow queries",
        auth_required: "JWT",
        url: "/analytics/api/v2/slow-queries/",
        methods: [{ method: "GET", response: j({ success: true }) }],
      },
      {
        name: "Endpoint volume",
        auth_required: "JWT",
        url: "/analytics/api/v2/endpoint-volume/",
        methods: [{ method: "GET", response: j({ success: true }) }],
      },
      {
        name: "Operation breakdown",
        auth_required: "JWT",
        url: "/analytics/api/v2/operation-breakdown/",
        methods: [{ method: "GET", response: j({ success: true }) }],
      },
      {
        name: "Storage trend",
        auth_required: "JWT",
        url: "/analytics/api/v2/storage-trend/",
        methods: [{ method: "GET", response: j({ success: true }) }],
      },
    ],
  },
];
