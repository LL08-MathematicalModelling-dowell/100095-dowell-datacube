"""
API documentation for the DataCube platform.
This data is structured for rendering on the API documentation page.
"""

from django.urls import reverse_lazy

apis = [
    {
        "group": "Authentication API",
        "description": "Endpoints for user registration, login, and token management. These endpoints are the entry point for interacting with DataCube.",
        "endpoints": [
            {
                "name": "Register User",
                "description": "Create a new user account. A verification email will be sent upon successful registration.",
                "auth_required": "No",
                "url": reverse_lazy("core:register"),
                "methods": [
                    {
                        "method": "POST",
                        "body": """{
    "email": "developer@example.com",
    "firstName": "Alex",
    "lastName": "Dev",
    "password": "a-strong-and-secure-password"
}""",
                        "response": """{
    "message": "User registered successfully. Please check your email to verify your account."
}"""
                    }
                ]
            },
            {
                "name": "Login (Get JWT)",
                "description": "Authenticate with your email and password to receive a short-lived Access Token and a long-lived Refresh Token.",
                "auth_required": "No",
                "url": reverse_lazy("core:login"),
                "methods": [
                    {
                        "method": "POST",
                        "body": """{
    "email": "developer@example.com",
    "password": "a-strong-and-secure-password"
}""",
                        "response": """{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI..."
}"""
                    }
                ]
            }
        ]
    },
    {
        "group": "Management API",
        "description": "Endpoints for managing your account, databases, and API keys. All requests to this API group must be authenticated using a JWT Bearer Token obtained from the Login endpoint.",
        "auth_header": "Authorization: Api-Key <YOUR_API_KEY>",
        "endpoints": [
            {
                "name": "Create Database",
                "description": "Create a new logical database with its initial collections and schema.",
                "auth_required": "API Key",
                "url": reverse_lazy("api:create_database"),
                "methods": [
                    {
                        "method": "POST",
                        "body": """{
    "db_name": "my_customer_project",
    "collections": [
        {
            "name": "users",
            "fields": [
                {"name": "email", "type": "string"},
                {"name": "signup_date", "type": "date"}
            ]
        }
    ]
}""",
                        "response": """{
    "success": true,
    "database": {
        "id": "60c72b2f9b1d8b1a2d3e4567",
        "name": "my_customer_project"
    },
    "collections": [ ... ]
}"""
                    }
                ]
            },
            {
                "name": "List Databases",
                "description": "Retrieve a paginated list of all logical databases you own.",
                "auth_required": "API Key",
                "url": reverse_lazy("api:list_databases"),
                "methods": [
                    {
                        "method": "GET",
                        "params": "page=1&page_size=10&search=customer",
                        "response": """{
    "success": true,
    "data": [
        {
            "id": "60c72b2f9b1d8b1a2d3e4567",
            "name": "my_customer_project",
            "num_collections": 1
        }
    ],
    "pagination": { ... }
}"""
                    }
                ]
            },
            {
                "name": "Get Database Metadata",
                "description": "Fetch the complete metadata document for a single database, including its schema.",
                "auth_required": "API Key",
                "url": reverse_lazy("api:get_metadata"),
                "methods": [
                    {
                        "method": "GET",
                        "params": "database_id=60c72b2f9b1d8b1a2d3e4567",
                        "response": """{
    "success": true,
    "data": {
        "_id": "60c72b2f9b1d8b1a2d3e4567",
        "user_id": "...",
        "displayName": "my_customer_project",
        "dbName": "my_customer_project_689547_V2",
        "collections": [ ... ]
    }
}"""
                    }
                ]
            },
            {
                "name": "List Collections",
                "description": "Retrieve all collections in a database along with their live document counts.",
                "auth_required": "API Key",
                "url": reverse_lazy("api:list_collections"),
                "methods": [
                    {
                        "method": "GET",
                        "params": "database_id=60c72b2f9b1d8b1a2d3e4567",
                        "response": """{
    "success": true,
    "collections": [
        {"name": "users", "num_documents": 152},
        {"name": "products", "num_documents": 840}
    ]
}"""
                    }
                ]
            },
            {
                "name": "Drop Database",
                "description": "Permanently delete a logical database and all of its collections and documents.",
                "auth_required": "JWT Bearer Token",
                "url": reverse_lazy("api:drop_database"),
                "methods": [
                    {
                        "method": "DELETE",
                        "body": """{
    "database_id": "60c72b2f9b1d8b1a2d3e4567",
    "confirmation": "my_customer_project"
}""",
                        "response": """{
    "success": true,
    "message": "Database 'my_customer_project' was successfully dropped."
}"""
                    }
                ]
            },
            {
                "name": "Drop Collections",
                "description": "Permanently delete one or more collections from a database.",
                "auth_required": "JWT Bearer Token",
                "url": reverse_lazy("api:drop_collections"),
                "methods": [
                    {
                        "method": "DELETE",
                        "body": """{
    "database_id": "60c72b2f9b1d8b1a2d3e4567",
    "collection_names": ["old_logs", "temporary_users"]
}""",
                        "response": """{
    "success": true,
    "dropped_collections": ["old_logs", "temporary_users"]
}"""
                    }
                ]
            },
            {
                "name": "Import Data (File Upload)",
                "description": "Bulk import documents into a collection from a JSON file.",
                "auth_required": "JWT Bearer Token",
                "url": reverse_lazy("api:import_data"),
                "methods": [
                    {
                        "method": "POST",
                        "body": """# This is a multipart/form-data request
{
    "database_id": "60c72b2f9b1d8b1a2d3e4567",
    "collection_name": "events",  # optional
    "json_file": (binary content of your .json file)
}""",
                        "response": """{
    "success": true,
    "collection": "events",
    "inserted_count": 5210
}"""
                    }
                ]
            }
        ]
    },

    {
        "group": "Data API",
        "description": "Endpoints for all programmatic Create, Read, Update, and Delete (CRUD) operations on your documents. All requests to this API group must be authenticated using an API Key.",
        "auth_header": "Authorization: Api-Key <YOUR_API_KEY>",
        "how_to_get_key": "API Keys can be generated in your user dashboard after logging in. They are long-lived and designed for use in your backend services, scripts, and applications.",
        "endpoints": [
            {
                "name": "CRUD Documents",
                "description": "Perform operations on documents within a specific collection.",
                "auth_required": "API Key",
                "url": reverse_lazy("api:crud"),
                "methods": [
                    {
                        "method": "POST (Create)",
                        "body": """{
    "database_id": "60c72b2f9b1d8b1a2d3e4567",
    "collection_name": "users",
    "data": [
        {"email": "alice@example.com", "signup_date": "2023-10-27T10:00:00Z"},
        {"email": "bob@example.com", "signup_date": "2023-10-27T11:00:00Z"}
    ]
}""",
                        "response": """{
    "success": true,
    "inserted_ids": ["..."]
}"""
                    },
                    {
                        "method": "GET (Read)",
                        "params": "database_id=...&collection_name=...&filters={\"email\": \"alice@example.com\"}",
                        "response": """{
    "success": true,
    "data": [ ... ],
    "pagination": { ... }
}"""
                    },
                    {
                        "method": "PUT (Update)",
                        "body": """{
    "database_id": "60c72b2f9b1d8b1a2d3e4567",
    "collection_name": "users",
    "filters": {"email": "alice@example.com"},
    "update_data": {"newsletter_subscribed": true}
}""",
                        "response": """{
    "success": true,
    "modified_count": 1
}"""
                    }
                ]
            }
        ]
    }
]