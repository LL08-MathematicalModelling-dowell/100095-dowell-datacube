// frontend/api-docs.ts

export interface ApiMethod {
  method: string;          // e.g., "POST", "GET", "PUT", "DELETE"
  body?: string;           // JSON string or multipart form description
  params?: string;         // Query parameters as string (e.g., "page=1&page_size=10")
  response: string;        // JSON string for example response
}

export interface ApiEndpoint {
  name: string;
  description: string;
  auth_required: string;   // "No", "API Key", "JWT Bearer Token", or "Signed URL"
  url: string;             // Static URL (e.g., "/api/v2/crud")
  methods: ApiMethod[];
  notes?: string;          // Additional guidance, e.g., file size limits, signed URL expiry
}

export interface ApiGroup {
  group: string;
  description: string;
  auth_header?: string;    // e.g., "Authorization: Api-Key <YOUR_API_KEY>"
  how_to_get_key?: string;
  endpoints: ApiEndpoint[];
}

export const apiDocs: ApiGroup[] = [
  {
    group: "Management API",
    description:
      "Endpoints for managing your logical databases, collections, and API keys. All requests in this group require an API Key (long‑lived) or a JWT (short‑lived). For third‑party integrations, we recommend using an API Key generated from your dashboard.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    how_to_get_key:
      "Log into your DataCube account, navigate to 'API Keys', and generate a new key. The key is shown only once – store it securely.",
    endpoints: [
      {
        name: "Create Database",
        description:
          "Create a new logical database with initial collections and optional field schemas.",
        auth_required: "API Key",
        url: "/api/v2/create_database",
        methods: [
          {
            method: "POST",
            body: JSON.stringify(
              {
                db_name: "my_customer_project",
                collections: [
                  {
                    name: "users",
                    fields: [
                      { name: "email", type: "string" },
                      { name: "signup_date", type: "date" },
                    ],
                  },
                ],
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                database: {
                  id: "60c72b2f9b1d8b1a2d3e4567",
                  name: "my_customer_project",
                },
                collections: ["users"],
              },
              null,
              2
            ),
          },
        ],
        notes:
          "The returned `database.id` should be used in all subsequent requests.",
      },
      {
        name: "List Databases",
        description:
          "Retrieve a paginated list of all logical databases you own. Supports search by name.",
        auth_required: "API Key",
        url: "/api/v2/list_databases",
        methods: [
          {
            method: "GET",
            params: "page=1&page_size=10&search=customer",
            response: JSON.stringify(
              {
                success: true,
                data: [
                  {
                    id: "60c72b2f9b1d8b1a2d3e4567",
                    name: "my_customer_project",
                    num_collections: 1,
                  },
                ],
                pagination: {
                  page: 1,
                  page_size: 10,
                  total_items: 1,
                  total_pages: 1,
                },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Get Database Metadata",
        description:
          "Fetch the complete metadata document for a single database, including its schema and collection details.",
        auth_required: "API Key",
        url: "/api/v2/get_metadata",
        methods: [
          {
            method: "GET",
            params: "database_id=60c72b2f9b1d8b1a2d3e4567",
            response: JSON.stringify(
              {
                success: true,
                data: {
                  _id: "60c72b2f9b1d8b1a2d3e4567",
                  user_id: "user_69a68586...",
                  displayName: "my_customer_project",
                  dbName: "my_customer_project_689547_V2",
                  collections: [
                    {
                      name: "users",
                      fields: [
                        { name: "email", type: "string" },
                        { name: "signup_date", type: "date" },
                      ],
                      document_count: 152,
                    },
                  ],
                },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Drop Database",
        description:
          "Permanently delete a logical database and all of its collections and documents. **This action is irreversible.**",
        auth_required: "API Key",
        url: "/api/v2/drop_database",
        methods: [
          {
            method: "DELETE",
            body: JSON.stringify(
              {
                database_id: "60c72b2f9b1d8b1a2d3e4567",
                confirmation: "my_customer_project",
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                message: "Database 'my_customer_project' was successfully dropped.",
              },
              null,
              2
            ),
          },
        ],
        notes:
          "You must provide the exact database name in the `confirmation` field to prevent accidental deletion.",
      },
      {
        name: "Add Collections",
        description:
          "Add one or more new collections to an existing database. Optionally define field schemas for indexing.",
        auth_required: "API Key",
        url: "/api/v2/add_collection",
        methods: [
          {
            method: "POST",
            body: JSON.stringify(
              {
                database_id: "60c72b2f9b1d8b1a2d3e4567",
                collections: [
                  {
                    name: "products",
                    fields: [
                      { name: "name", type: "string" },
                      { name: "price", type: "number" },
                    ],
                  },
                ],
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                collections: ["products"],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "List Collections",
        description:
          "Retrieve all collections in a database along with their live document counts (real‑time from the underlying MongoDB).",
        auth_required: "API Key",
        url: "/api/v2/list_collections",
        methods: [
          {
            method: "GET",
            params: "database_id=60c72b2f9b1d8b1a2d3e4567",
            response: JSON.stringify(
              {
                success: true,
                collections: [
                  { name: "users", num_documents: 152 },
                  { name: "products", num_documents: 840 },
                ],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Drop Collections",
        description: "Permanently delete one or more collections from a database.",
        auth_required: "API Key",
        url: "/api/v2/drop_collections",
        methods: [
          {
            method: "DELETE",
            body: JSON.stringify(
              {
                database_id: "60c72b2f9b1d8b1a2d3e4567",
                collection_names: ["old_logs", "temporary_users"],
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                dropped: ["old_logs", "temporary_users"],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Import Data (JSON File)",
        description:
          "Bulk import documents from a JSON file into a collection. If the collection does not exist, it is created automatically with an inferred schema.",
        auth_required: "API Key",
        url: "/api/v2/import_data",
        methods: [
          {
            method: "POST",
            body: `Content-Type: multipart/form-data

Fields:
- database_id (string)
- collection_name (optional string)
- json_file (binary content of .json file)`,
            response: JSON.stringify(
              {
                success: true,
                collection: "events",
                inserted_count: 5210,
              },
              null,
              2
            ),
          },
        ],
        notes:
          "The JSON file must contain either a single JSON object or an array of objects. Maximum file size is 50MB (configurable).",
      },
    ],
  },
  {
    group: "Data API (CRUD)",
    description:
      "Endpoints for all programmatic Create, Read, Update, and Delete operations on your documents. All requests require an API Key (long‑lived) for authentication.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    endpoints: [
      {
        name: "CRUD Operations",
        description:
          "Perform operations on documents within a specific collection. The HTTP method determines the action.",
        auth_required: "API Key",
        url: "/api/v2/crud",
        methods: [
          {
            method: "POST (Create)",
            body: JSON.stringify(
              {
                database_id: "60c72b2f9b1d8b1a2d3e4567",
                collection_name: "users",
                documents: [
                  { email: "alice@example.com", signup_date: "2023-10-27T10:00:00Z" },
                  { email: "bob@example.com", signup_date: "2023-10-27T11:00:00Z" },
                ],
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                inserted_ids: ["65e8a5b2f1d8b1a2d3e45678", "65e8a5b2f1d8b1a2d3e45679"],
              },
              null,
              2
            ),
          },
          {
            method: "GET (Read)",
            params:
              "database_id=60c72b2f9b1d8b1a2d3e4567&collection_name=users&filters=%7B%22email%22:%22alice@example.com%22%7D&page=1&page_size=20",
            response: JSON.stringify(
              {
                success: true,
                data: [{ email: "alice@example.com", signup_date: "2023-10-27T10:00:00Z" }],
                pagination: {
                  page: 1,
                  page_size: 20,
                  total_items: 1,
                  total_pages: 1,
                },
              },
              null,
              2
            ),
          },
          {
            method: "PUT (Update)",
            body: JSON.stringify(
              {
                database_id: "60c72b2f9b1d8b1a2d3e4567",
                collection_name: "users",
                filters: { email: "alice@example.com" },
                update_data: { newsletter_subscribed: true },
                update_all_fields: false,
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                modified_count: 1,
              },
              null,
              2
            ),
          },
          {
            method: "DELETE (Delete)",
            body: JSON.stringify(
              {
                database_id: "60c72b2f9b1d8b1a2d3e4567",
                collection_name: "users",
                filters: { email: "alice@example.com" },
                soft_delete: true,
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                success: true,
                count: 1,
              },
              null,
              2
            ),
          },
        ],
        notes:
          "For read operations, filters must be a URL‑encoded JSON string. For updates, `update_all_fields` controls whether to replace the entire document (true) or only specified fields (false).",
      },
    ],
  },
  {
    group: "File Storage API (GridFS)",
    description:
      "High‑performance large file storage using MongoDB GridFS. Files are stored in a shared high‑availability bucket and indexed by user ownership. Supports streaming uploads/downloads and automatic signed URLs for secure embedding.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    endpoints: [
      {
        name: "List Files",
        description:
          "Retrieve a paginated list of file metadata along with global storage statistics for the authenticated user. Each file entry includes a **signed URL** that can be used directly in `<img>`, `<video>`, or `<a>` tags for 5 Hours.",
        auth_required: "API Key",
        url: "/api/v2/files/",
        methods: [
          {
            method: "GET",
            params: "page=1&page_size=10&search=report",
            response: JSON.stringify(
              {
                success: true,
                data: [
                  {
                    _id: "65e8a5b2f1d8b1a2d3e45678",
                    filename: "annual_report_2023.pdf",
                    length: 1048576,
                    contentType: "application/pdf",
                    uploadDate: "2024-03-05T12:00:00Z",
                    signed_url:
                      "/api/v2/files/65e8a5b2f1d8b1a2d3e45678/stream/?expires=1743828000&sig=abc123...",
                  },
                ],
                stats: {
                  total_files: 15,
                  total_storage_bytes: 52428800,
                },
                pagination: {
                  current_page: 1,
                  page_size: 10,
                  total_items: 15,
                  total_pages: 2,
                },
              },
              null,
              2
            ),
          },
        ],
        notes:
          "The signed URL expires after 7 days. For long‑lived access, regenerate the URL using the file detail endpoint.",
      },
      {
        name: "Upload File",
        description:
          "Stream a file to GridFS using multipart/form-data. Automatically checks storage quota and updates user metadata.",
        auth_required: "API Key",
        url: "/api/v2/files/",
        methods: [
          {
            method: "POST",
            body: `Content-Type: multipart/form-data

Fields:
- file: (binary data)
- filename: (optional) string
- content_type: (optional) string`,
            response: JSON.stringify(
              {
                success: true,
                file_id: "65e8a5b2f1d8b1a2d3e45678",
                filename: "annual_report_2023.pdf",
                file_size: 1048576,
                signed_url:
                  "/api/v2/files/65e8a5b2f1d8b1a2d3e45678/stream/?expires=1743828000&sig=abc123...",
              },
              null,
              2
            ),
          },
        ],
        notes: "Maximum file size is determined by your plan (default 500MB).",
      },
      {
        name: "Get File Detail",
        description:
          "Retrieve metadata for a specific file, including a fresh signed URL (valid for 24 Hours).",
        auth_required: "API Key",
        url: "/api/v2/files/:file_id/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                info: {
                  _id: "65e8a5b2f1d8b1a2d3e45678",
                  filename: "annual_report_2023.pdf",
                  uploadDate: "2024-03-05T12:00:00Z",
                  length: 1048576,
                  contentType: "application/pdf",
                  metadata: { user_id: "user_69a68586..." },
                  signed_url:
                    "/api/v2/files/65e8a5b2f1d8b1a2d3e45678/stream/?expires=1743828600&sig=def456...",
                },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Stream File (Embed & Play)",
        description:
          "Stream the binary content of a file using a signed URL. Supports HTTP range requests (seeking), making it perfect for `<video>`, `<audio>`, and `<img>` tags. The signed URL is generated automatically by the list/detail endpoints.",
        auth_required: "Signed URL (no API Key needed in the request)",
        url: "/api/v2/files/:file_id/stream/?expires=...&sig=...",
        methods: [
          {
            method: "GET",
            response: "(Binary stream; Content-Type matches the uploaded file's MIME type)",
          },
        ],
        notes:
          "You do not need to add an `Authorization` header when using a signed URL – the signature and expiration provide secure access. The URL is valid for 24 Hours; after that, fetch a fresh one from the file detail endpoint.",
      },
      {
        name: "Download File (Small Files)",
        description:
          "Download the entire file as an attachment. **Only suitable for files under 20MB.** For larger files, use the Stream endpoint.",
        auth_required: "Signed URL",
        url: "/api/v2/files/:file_id/download/?expires=...&sig=...",
        methods: [
          {
            method: "GET",
            response: "(Binary stream with Content-Disposition: attachment)",
          },
        ],
        notes:
          "If the file exceeds 20MB, the API returns `413 Payload Too Large`. In that case, use the Stream endpoint and add `?download=1` to force attachment behavior.",
      },
      {
        name: "Delete File",
        description:
          "Permanently remove a file and all its chunks from GridFS.",
        auth_required: "API Key",
        url: "/api/v2/files/:file_id/",
        methods: [
          {
            method: "DELETE",
            response: JSON.stringify(
              {
                success: true,
                message: "File deleted",
              },
              null,
              2
            ),
          },
        ],
      },
    ],
  },
  {
    group: "Analytics API (Dashboard)",
    description:
      "Endpoints for fetching usage metrics, performance data, and error analytics for your account. These power the DataCube dashboard and are intended for internal use (but can be used by third‑party tools). All requests require an API Key.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    endpoints: [
      {
        name: "Dashboard Overview",
        description:
          "Get summary metrics: total requests, average response time, error rate, and total storage used, plus daily request counts for the last 7 days.",
        auth_required: "API Key",
        url: "/analytics/api/v2/dashboard/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                overview: {
                  total_requests: 152340,
                  avg_response_time_ms: 124.5,
                  error_rate_percent: 0.23,
                  total_storage_mb: 245.8,
                },
                daily_requests: {
                  dates: ["2025-04-01", "2025-04-02", "2025-04-03"],
                  counts: [21450, 22100, 19800],
                  avg_durations_ms: [120.2, 125.1, 118.7],
                },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Performance Metrics",
        description:
          "Response time percentiles (p50, p90, p95, p99) and throughput (requests per hour) for the last 7 days.",
        auth_required: "API Key",
        url: "/analytics/api/v2/performance/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                percentiles_ms: {
                  p50: 112.3,
                  p90: 245.6,
                  p95: 398.2,
                  p99: 890.1,
                },
                throughput_last_24h: [
                  { hour: "2025-04-03 00:00", requests: 342 },
                  { hour: "2025-04-03 01:00", requests: 298 },
                ],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Error Analytics",
        description: "Breakdown of errors by HTTP status code, endpoint, and error type (client vs server).",
        auth_required: "API Key",
        url: "/analytics/api/v2/errors/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                errors_by_status_code: { "400": 45, "401": 12, "500": 3 },
                top_error_endpoints: [
                  { path: "/api/v2/crud", errors: 32 },
                  { path: "/api/v2/files/", errors: 18 },
                ],
                error_types: { client_error: 57, server_error: 3 },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Top Collections",
        description: "Most frequently accessed collections (by number of operations) in the last 7 days.",
        auth_required: "API Key",
        url: "/analytics/api/v2/top-collections/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                top_collections: [
                  { name: "users", operations: 45230 },
                  { name: "events", operations: 32100 },
                ],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Slow Queries",
        description: "Paginated list of slow queries that exceeded the defined threshold (e.g., >1s).",
        auth_required: "API Key",
        url: "/analytics/api/v2/slow-queries/",
        methods: [
          {
            method: "GET",
            params: "limit=20&offset=0",
            response: JSON.stringify(
              {
                success: true,
                data: [
                  {
                    id: "65e8a5b2f1d8b1a2d3e45678",
                    duration_ms: 2350.4,
                    threshold_ms: 1000,
                    collection: "logs",
                    query_details: {
                      method: "POST",
                      path: "/api/v2/crud",
                      params: { page: 1 },
                    },
                    timestamp: "2025-04-03T14:32:10Z",
                  },
                ],
                pagination: { total: 12, limit: 20, offset: 0 },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Endpoint Volume",
        description: "Request count per endpoint (bar chart data) for the last 7 days.",
        auth_required: "API Key",
        url: "/analytics/api/v2/endpoint-volume/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                endpoint_volume: [
                  { endpoint: "/api/v2/crud", requests: 85430 },
                  { endpoint: "/api/v2/files/", requests: 12340 },
                ],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Operation Breakdown",
        description:
          "Pie chart data: distribution of database operations (insert, query, update, delete, etc.) over the last 7 days.",
        auth_required: "API Key",
        url: "/analytics/api/v2/operation-breakdown/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                operation_breakdown: {
                  document_query: 62340,
                  document_creation: 12450,
                  document_update: 8930,
                  document_deletion: 2100,
                  data_import: 85,
                },
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Storage Trend",
        description: "Daily storage usage over the last 30 days (in MB).",
        auth_required: "API Key",
        url: "/analytics/api/v2/storage-trend/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                storage_trend_mb: [
                  { date: "2025-03-01", storage_mb: 210.5 },
                  { date: "2025-03-02", storage_mb: 212.3 },
                ],
              },
              null,
              2
            ),
          },
        ],
      },
    ],
  },
];