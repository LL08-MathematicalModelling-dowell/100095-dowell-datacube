/**
 * Developer-facing API reference (integration / automation).
 * Account UI flows (register, OTP, OAuth, profile) and dashboard analytics are documented in
 * `datacube_documentation.md` at the repository root.
 */

import type { AuthMode } from "../lib/apiSamples";

export interface ApiMethod {
  method: string;
  body?: string;
  params?: string;
  response: string;
  /** Drives code-sample auth header generation. */
  auth_mode?: AuthMode;
  multipart?: boolean;
}

export interface ApiEndpoint {
  name: string;
  description?: string;
  auth_required?: string;
  auth_mode?: AuthMode;
  url: string;
  methods: ApiMethod[];
  notes?: string;
}

export interface ApiGroup {
  group: string;
  description: string;
  auth_header?: string;
  how_to_get_key?: string;
  default_auth_mode?: AuthMode;
  endpoints: ApiEndpoint[];
}

const j = (o: unknown) => JSON.stringify(o, null, 2);

const DB_ID = "507f1f77bcf86cd799439011";
const DOC_ID = "674a1b2c3d4e5f6789012345";
const FILE_ID = "674a1b2c3d4e5f6789012346";

export const apiDocs: ApiGroup[] = [
  {
    group: "Authentication (`/core/`)",
    description:
      "Obtain JWTs for interactive apps or create API keys for server-to-server automation. Email must be verified before data API access.",
    auth_header: "Authorization: Bearer <access_token>",
    how_to_get_key:
      "POST /core/login/ with email and password, or use POST /core/api/v1/keys/ (JWT) to mint an API key: Authorization: Api-Key <key>.",
    default_auth_mode: "bearer",
    endpoints: [
      {
        name: "Login",
        auth_required: "None",
        auth_mode: "none",
        description: "Password login. Returns access + refresh JWTs and user metadata.",
        url: "/core/login/",
        methods: [
          {
            method: "POST",
            auth_mode: "none",
            body: j({ email: "dev@example.com", password: "minimum8chars" }),
            response: j({
              access: "<jwt>",
              refresh: "<jwt>",
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
        auth_mode: "none",
        description: "Exchange a refresh token for a new access token.",
        url: "/core/auth/token/refresh/",
        methods: [
          {
            method: "POST",
            auth_mode: "none",
            body: j({ refresh: "<refresh_token>" }),
            response: j({ access: "<new_access_token>" }),
          },
        ],
      },
      {
        name: "API keys",
        auth_required: "JWT",
        description:
          "Manage integration keys. POST returns the full secret once — store it securely.",
        url: "/core/api/v1/keys/",
        methods: [
          {
            method: "GET",
            auth_mode: "bearer",
            response: j([
              {
                _id: "…",
                name: "CI pipeline",
                key_display: "sk_test_****abcd",
                is_active: true,
                created_at: "2026-05-15T12:00:00Z",
              },
            ]),
          },
          {
            method: "POST",
            auth_mode: "bearer",
            body: j({ name: "CI pipeline" }),
            response: j({
              key: "sk_test_…",
              name: "CI pipeline",
              id: "…",
            }),
          },
        ],
        notes: "Revoke: DELETE /core/api/v1/keys/<key_id>/ with JWT.",
      },
    ],
  },
  {
    group: "Data API (`/api/v2/`)",
    description:
      "Databases, collections, documents (CRUD), and GridFS file storage. Authenticate with JWT or API key. Analyst role is read-only on mutating routes.",
    auth_header: "Authorization: Bearer <access_token>  — or —  Authorization: Api-Key <key>",
    default_auth_mode: "bearer",
    endpoints: [
      {
        name: "Health check",
        auth_required: "None",
        auth_mode: "none",
        url: "/api/v2/health_check/",
        methods: [
          {
            method: "GET",
            auth_mode: "none",
            response: j({
              success: true,
              status: "healthy",
              timestamp: "2026-05-15T12:00:00",
            }),
          },
        ],
      },
      {
        name: "Create database",
        auth_required: "JWT or API key — developer/admin",
        description: "Provision a logical database and optional initial collections with field hints.",
        url: "/api/v2/create_database/",
        methods: [
          {
            method: "POST",
            body: j({
              db_name: "my_app",
              collections: [
                {
                  name: "users",
                  fields: [
                    { name: "email", type: "string" },
                    { name: "age", type: "number" },
                  ],
                },
              ],
            }),
            response: j({
              success: true,
              database: { id: DB_ID, name: "my_app" },
              collections: ["users"],
            }),
          },
        ],
      },
      {
        name: "List databases",
        auth_required: "JWT or API key",
        url: "/api/v2/list_databases/",
        methods: [
          {
            method: "GET",
            params: "page=1&page_size=50&search=",
            response: j({
              success: true,
              data: [{ id: DB_ID, displayName: "my_app" }],
              pagination: {
                page: 1,
                page_size: 50,
                total_items: 1,
                total_pages: 1,
              },
            }),
          },
        ],
      },
      {
        name: "List collections",
        auth_required: "JWT or API key",
        url: "/api/v2/list_collections/",
        methods: [
          {
            method: "GET",
            params: `database_id=${DB_ID}`,
            response: j({
              success: true,
              data: [{ name: "users", document_count: 42 }],
            }),
          },
        ],
      },
      {
        name: "Get metadata",
        auth_required: "JWT or API key",
        description: "Full metadata document (collections, field types, quotas).",
        url: "/api/v2/get_metadata/",
        methods: [
          {
            method: "GET",
            params: `database_id=${DB_ID}`,
            response: j({ success: true, data: { displayName: "my_app", collections: {} } }),
          },
        ],
      },
      {
        name: "Add collections",
        auth_required: "JWT or API key — developer/admin",
        url: "/api/v2/add_collection/",
        methods: [
          {
            method: "POST",
            body: j({
              database_id: DB_ID,
              collections: [
                {
                  name: "orders",
                  fields: [{ name: "total", type: "number" }],
                },
              ],
            }),
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "CRUD — insert",
        auth_required: "JWT or API key — developer/admin",
        description: "Insert up to 500 documents per request. Use `documents` (not `data`).",
        url: "/api/v2/crud/",
        methods: [
          {
            method: "POST",
            body: j({
              database_id: DB_ID,
              collection_name: "users",
              documents: [{ email: "alice@example.com", status: "active" }],
            }),
            response: j({ success: true, inserted_ids: [DOC_ID] }),
          },
        ],
      },
      {
        name: "CRUD — query",
        auth_required: "JWT or API key",
        description: "Paginated query; `filters` is a JSON object in the query string.",
        url: "/api/v2/crud/",
        methods: [
          {
            method: "GET",
            params: `database_id=${DB_ID}&collection_name=users&filters={}&page=1&page_size=50`,
            response: j({
              success: true,
              data: [{ _id: DOC_ID, email: "alice@example.com" }],
              pagination: { page: 1, page_size: 50, total_items: 1, total_pages: 1 },
            }),
          },
        ],
      },
      {
        name: "CRUD — update",
        auth_required: "JWT or API key — developer/admin",
        description:
          "Single-doc updates require `_id` in filters unless `update_many` is true. `upsert` cannot be combined with `update_many` — use bulk update for mixed per-document sync.",
        url: "/api/v2/crud/",
        methods: [
          {
            method: "PUT",
            body: j({
              database_id: DB_ID,
              collection_name: "users",
              filters: { _id: DOC_ID },
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
        ],
      },
      {
        name: "CRUD — bulk update / upsert",
        auth_required: "JWT or API key — developer/admin",
        description:
          "Sync many documents in one request. Each operation is an independent updateOne with optional upsert (requires `_id` and `update_all_fields: true`). Max 500 operations.",
        url: "/api/v2/crud/bulk/",
        methods: [
          {
            method: "POST",
            body: j({
              database_id: DB_ID,
              collection_name: "users",
              operations: [
                {
                  filters: { _id: DOC_ID },
                  update_data: { points: 120 },
                  update_all_fields: true,
                  upsert: true,
                },
                {
                  filters: { _id: "674a1b2c3d4e5f6789012346" },
                  update_data: { points: 450 },
                  update_all_fields: true,
                  upsert: true,
                },
              ],
            }),
            response: j({
              success: true,
              matched_count: 1,
              modified_count: 1,
              upserted_count: 1,
              results: [
                { index: 0, ok: true },
                { index: 1, ok: true, upserted_id: "674a1b2c3d4e5f6789012347" },
              ],
            }),
          },
        ],
      },
      {
        name: "CRUD — delete",
        auth_required: "JWT or API key — developer/admin",
        description: "Soft delete by default (`is_deleted: true`). Filters required.",
        url: "/api/v2/crud/",
        methods: [
          {
            method: "DELETE",
            body: j({
              database_id: DB_ID,
              collection_name: "users",
              filters: { _id: DOC_ID },
              soft_delete: true,
            }),
            response: j({ success: true, count: 1 }),
          },
        ],
      },
      {
        name: "Files — list & upload",
        auth_required: "JWT or API key",
        description: "GridFS-backed object storage for arbitrary binaries.",
        url: "/api/v2/files/",
        methods: [
          {
            method: "GET",
            params: "page=1&page_size=50&search=",
            response: j({
              success: true,
              data: [{ file_id: FILE_ID, filename: "report.pdf", size: 1024 }],
            }),
          },
          {
            method: "POST",
            multipart: true,
            body: "multipart: file (required), optional filename, content_type",
            response: j({ success: true, file_id: FILE_ID }),
          },
        ],
        notes:
          "GET /api/v2/files/<file_id>/ — metadata. DELETE same path. Stream: GET /api/v2/files/stream/<file_id>/ — download: GET /api/v2/files/download/<file_id>/ (signed URL params when enforced).",
      },
      {
        name: "Import JSON",
        auth_required: "JWT or API key — developer/admin",
        url: "/api/v2/import_data/",
        methods: [
          {
            method: "POST",
            multipart: true,
            body: "multipart: json_file, database_id, optional collection_name",
            response: j({ success: true, imported: 100 }),
          },
        ],
      },
      {
        name: "Drop collections",
        auth_required: "JWT or API key — developer/admin",
        url: "/api/v2/drop_collections/",
        methods: [
          {
            method: "DELETE",
            body: j({
              database_id: DB_ID,
              collection_names: ["legacy_events"],
            }),
            response: j({ success: true }),
          },
        ],
      },
      {
        name: "Drop database",
        auth_required: "JWT or API key — developer/admin",
        description: "`confirmation` must match the database display name exactly.",
        url: "/api/v2/drop_database/",
        methods: [
          {
            method: "DELETE",
            body: j({
              database_id: DB_ID,
              confirmation: "my_app",
            }),
            response: j({ success: true }),
          },
        ],
      },
    ],
  },
];
