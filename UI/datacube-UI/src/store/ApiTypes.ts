export interface ApiMethod {
  method: string; // e.g., "POST", "GET", "PUT", "DELETE"
  body?: string; // JSON string or multipart form description
  params?: string; // Query parameters as string (e.g., "page=1&page_size=10")
  response: string; // JSON string for example response
}

export interface ApiEndpoint {
  name: string;
  description: string;
  auth_required: string; // e.g., "No", "API Key", "JWT Bearer Token"
  url: string; // Static URL (e.g., "/api/register")
  methods: ApiMethod[];
  notes?: string; // Optional for future extensibility
}

export interface ApiGroup {
  group: string;
  description: string;
  auth_header?: string; // e.g., "Authorization: Api-Key <YOUR_API_KEY>"
  how_to_get_key?: string;
  endpoints: ApiEndpoint[];
}

export const apiDocs: ApiGroup[] = [
  {
    group: "Authentication API",
    description:
      "Endpoints for user registration, login, and token management. These endpoints are the entry point for interacting with DataCube.",
    endpoints: [
      {
        name: "Register User",
        description:
          "Create a new user account. A verification email will be sent upon successful registration.",
        auth_required: "No",
        url: "/api/register",
        methods: [
          {
            method: "POST",
            body: JSON.stringify(
              {
                email: "developer@example.com",
                firstName: "Alex",
                lastName: "Dev",
                password: "a-strong-and-secure-password",
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                message:
                  "User registered successfully. Please check your email to verify your account.",
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Login (Get JWT)",
        description:
          "Authenticate with your email and password to receive a short-lived Access Token and a long-lived Refresh Token.",
        auth_required: "No",
        url: "/api/login",
        methods: [
          {
            method: "POST",
            body: JSON.stringify(
              {
                email: "developer@example.com",
                password: "a-strong-and-secure-password",
              },
              null,
              2
            ),
            response: JSON.stringify(
              {
                refresh: "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
                access: "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
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
    group: "Management API",
    description:
      "Endpoints for managing your account, databases, and API keys. All requests to this API group must be authenticated using a JWT Bearer Token obtained from the Login endpoint.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    endpoints: [
      {
        name: "Create Database",
        description:
          "Create a new logical database with its initial collections and schema.",
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
                collections: [],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "List Databases",
        description:
          "Retrieve a paginated list of all logical databases you own.",
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
                pagination: {},
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
          "Fetch the complete metadata document for a single database, including its schema.",
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
                  user_id: "...",
                  displayName: "my_customer_project",
                  dbName: "my_customer_project_689547_V2",
                  collections: [],
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
          "Permanently delete a logical database and all of its collections and documents.",
        auth_required: "JWT Bearer Token",
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
                message:
                  "Database 'my_customer_project' was successfully dropped.",
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Add Collections",
        description:
          "Add one or more new collections to an existing database.",
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
          },
        ],
      },
      {
        name: "List Collections",
        description:
          "Retrieve all collections in a database along with their live document counts.",
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
        description:
          "Permanently delete one or more collections from a database.",
        auth_required: "JWT Bearer Token",
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
                dropped_collections: ["old_logs", "temporary_users"],
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Import Data (File Upload)",
        description:
          "Bulk import documents into a collection from a JSON file.",
        auth_required: "JWT Bearer Token",
        url: "/api/import_data",
        methods: [
          {
            method: "POST",
            body: `# This is a multipart/form-data request
{
  "database_id": "60c72b2f9b1d8b1a2d3e4567",
  "collection_name": "events",
  "json_file": "(binary content of your .json file)"
}`,
            response: JSON.stringify(
              { success: true, collection: "events", inserted_count: 5210 },
              null,
              2
            ),
          },
        ],
      },
    ],
  },
  {
    group: "Data API",
    description:
      "Endpoints for all programmatic Create, Read, Update, and Delete (CRUD) operations on your documents. All requests to this API group must be authenticated using an API Key.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    how_to_get_key:
      "API Keys can be generated in your user dashboard after logging in. They are long-lived and designed for use in your backend services, scripts, and applications.",
    endpoints: [
      {
        name: "CRUD Documents",
        description:
          "Perform operations on documents within a specific collection.",
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
                  {
                    email: "alice@example.com",
                    signup_date: "2023-10-27T10:00:00Z",
                  },
                  {
                    email: "bob@example.com",
                    signup_date: "2023-10-27T11:00:00Z",
                  },
                ],
              },
              null,
              2
            ),
            response: JSON.stringify(
              { success: true, inserted_ids: ["..."] },
              null,
              2
            ),
          },
          {
            method: "GET (Read)",
            params:
              'database_id=...&collection_name=...&filters={"email": "alice@example.com"}',
            response: JSON.stringify(
              { success: true, data: [], pagination: {} },
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
              },
              null,
              2
            ),
            response: JSON.stringify(
              { success: true, modified_count: 1 },
              null,
              2
            ),
          },
        ],
      },
    ],
  },
  {
    group: "File Storage API (GridFS)",
    description:
      "Endpoints for high-performance large file storage using MongoDB GridFS. Files are stored in a shared high-availability bucket and indexed by user ownership. Supports streaming uploads and downloads with integrated storage telemetry.",
    auth_header: "Authorization: Api-Key <YOUR_API_KEY>",
    endpoints: [
      {
        name: "List Files",
        description: "Retrieve a paginated list of file metadata along with global storage statistics for the authenticated user.",
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
                    file_id: "65e8a5b2f1d8b1a2d3e45678",
                    filename: "annual_report_2023.pdf",
                    size: 1048576,
                    content_type: "application/pdf",
                    storage_type: "gridfs",
                    uploaded_at: "2024-03-05T12:00:00Z"
                  }
                ],
                stats: {
                  total_files: 15,
                  total_storage_bytes: 52428800
                },
                pagination: {
                  current_page: 1,
                  page_size: 10,
                  total_items: 15,
                  total_pages: 2
                }
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Upload File",
        description: "Stream a file to GridFS using multipart/form-data. Automatically calculates storage quota and updates user metadata.",
        auth_required: "API Key",
        url: "/api/v2/files/",
        methods: [
          {
            method: "POST",
            body: "Content-Type: multipart/form-data\n\nFields:\n- file: (Binary data)\n- filename: (Optional) string\n- content_type: (Optional) string",
            response: JSON.stringify(
              {
                success: true,
                file_id: "65e8a5b2f1d8b1a2d3e45678",
                filename: "annual_report_2023.pdf",
                file_size: 1048576
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Get File Detail",
        description: "Retrieve physical storage info (chunks, upload date) and ownership metadata for a specific file.",
        auth_required: "API Key",
        url: "/api/v2/files/:file_id/",
        methods: [
          {
            method: "GET",
            response: JSON.stringify(
              {
                success: true,
                info: {
                  filename: "annual_report_2023.pdf",
                  upload_date: "2024-03-05T12:00:00Z",
                  length: 1048576,
                  metadata: {
                    contentType: "application/pdf",
                    user_id: "user_69a68586..."
                  }
                }
              },
              null,
              2
            ),
          },
        ],
      },
      {
        name: "Download File",
        description: "Download the file in one go, with ownership verification and Content-Type header set for direct browser compatibility. Limits apply for files larger than 20MB to prevent memory issues.",
        auth_required: "API Key",
        url: "/api/v2/files/:file_id/download/",
        methods: [
          {
            method: "GET",
            response: "(Binary Stream: application/octet-stream or application/pdf)",
          },
        ],
        notes: "For files larger than 20MB, use the Stream File endpoint to avoid memory issues."
      },
       {
        name: "Stream File",
        description: "Stream the binary content of a file. Includes ownership verification and automatic Content-Type detection.",
        auth_required: "API Key",
        url: "/api/v2/files/:file_id/stream/",
        methods: [
          {
            method: "GET",
            response: "(Binary Stream: application/octet-stream or application/pdf)",
          },
        ],
        notes: "Uses StreamingHttpResponse to minimize memory footprint. Directly compatible with <a download> or <img src>."
      },
      {
        name: "Delete File",
        description: "Permanently remove file chunks from GridFS and cleanup the associated metadata document.",
        auth_required: "API Key",
        url: "/api/v2/files/:file_id/",
        methods: [
          {
            method: "DELETE",
            response: JSON.stringify(
              {
                success: true,
                message: "File deleted"
              },
              null,
              2
            ),
          },
        ],
      },
    ],
  }

];
