"""API documentation for a DataCube database management system."""

from django.urls import reverse

apis = [
    {
        "name": "Health Check",
        "description": "Verify that the API server is up and responding.",
        "url": reverse("api:health_check"),
        "methods": [
            {
                "method": "GET",
                "params": None,
                "body": None,
                "response": """
{
    "success": true,
    "message": "Server is up"
}
"""
            }
        ]
    },
    {
        "name": "Create Database",
        "description": "Create a new logical database and its initial collections/fields.",
        "url": reverse("api:create_database"),
        "methods": [
            {
                "method": "POST",
                "body": """
{
    "db_name": "new_database",
    "collections": [
        {
            "name": "users",
            "fields": [
                {"name": "username", "type": "string"},
                {"name": "age", "type": "number"}
            ]
        }
    ]
}
""",
                "response": """
{
    "success": true,
    "message": "Database 'new_database' and collections created successfully.",
    "database": {
        "id": "507f1f77bcf86cd799439011",
        "name": "new_database"
    },
    "collections": [
        {
            "name": "users",
            "id": "607e1c72e13c2a3f4a9b1234",
            "fields": [
                {"name": "username", "type": "string"},
                {"name": "age", "type": "number"}
            ]
        }
    ]
}
"""
            }
        ]
    },
    {
        "name": "Add Collections",
        "description": "Add new collections (with field definitions) to an existing database.",
        "url": reverse("api:add_collection"),
        "methods": [
            {
                "method": "POST",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "collections": [
        {
            "name": "orders",
            "fields": [
                {"name": "order_id", "type": "string"},
                {"name": "total", "type": "number"}
            ]
        }
    ]
}
""",
                "response": """
{
    "success": true,
    "message": "Collections 'orders' created successfully.",
    "collections": [
        {
            "name": "orders",
            "id": "607e1e33a1b2c4d5e6f78901",
            "fields": [
                {"name": "order_id", "type": "string"},
                {"name": "total", "type": "number"}
            ]
        }
    ],
    "database": {
        "total_collections": 2,
        "total_fields": 4
    }
}
"""
            }
        ]
    },
    {
        "name": "List Databases",
        "description": "Page through all databases with optional Mongo-style filter and collection count.",
        "url": reverse("api:list_databases"),
        "methods": [
            {
                "method": "POST",
                "body": """
{
    "page": 1,
    "page_size": 10,
    "filter": {
        "number_of_collections": { "$gte": 2 },
        "database_name": { "$regex": "^prod_" }
    }
}
""",
                "response": """
{
    "success": true,
    "data": [
        {"id": "507f1f77bcf86cd799439011", "database_name": "prod_users", "num_collections": 5},
        {"id": "507f1f77bcf86cd799439012", "database_name": "prod_orders", "num_collections": 3}
    ],
    "pagination": {
        "page": 1,
        "page_size": 10,
        "total": 2,
        "total_pages": 1
    }
}
"""
            }
        ]
    },
    {
        "name": "List Collections",
        "description": "Retrieve all collections in a database with document counts.",
        "url": reverse("api:list_collections"),
        "methods": [
            {
                "method": "GET",
                "params": {
                    "database_id": "507f1f77bcf86cd799439011"
                },
                "response": """
{
    "success": true,
    "collections": [
        {"name": "users", "num_documents": 42},
        {"name": "orders", "num_documents": 128}
    ]
}
"""
            }
        ]
    },
    {
        "name": "Get Database Metadata",
        "description": "Fetch metadata for a database including collections and fields.",
        "url": reverse("api:get_metadata"),
        "methods": [
            {
                "method": "GET",
                "params": {
                    "database_id": "507f1f77bcf86cd799439011"
                },
                "response": """
{
    "success": true,
    "data": {
        "_id": "507f1f77bcf86cd799439011",
        "database_name": "example_db",
        "number_of_collections": 2,
        "number_of_fields": 5,
        "collections": [
            {
                "name": "users",
                "fields": [
                    {"name": "username", "type": "string"},
                    {"name": "email", "type": "string"}
                ]
            },
            {
                "name": "orders",
                "fields": [
                    {"name": "order_id", "type": "string"},
                    {"name": "total", "type": "number"}
                ]
            }
        ]
    }
}
"""
            }
        ]
    },
    {
        "name": "Drop Database",
        "description": "Delete a database and all collections after confirmation.",
        "url": reverse("api:drop_database"),
        "methods": [
            {
                "method": "DELETE",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "confirmation": "example_db"
}
""",
                "response": """
{
    "success": true,
    "message": "Database 'example_db' and its metadata dropped successfully"
}
"""
            }
        ]
    },
    {
        "name": "Drop Collections",
        "description": "Remove one or more collections from a database.",
        "url": reverse("api:drop_collections"),
        "methods": [
            {
                "method": "DELETE",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_names": ["users", "orders"]
}
""",
                "response": """
{
    "success": true,
    "dropped_collections": ["users", "orders"],
    "failed_collections": []
}
"""
            }
        ]
    },
    {
        "name": "CRUD Documents",
        "description": "Create, read, update, and delete documents in a collection.",
        "url": reverse("api:crud"),
        "methods": [
            {
                "method": "POST",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "users",
    "data": [
        {"username": "alice", "age": 28},
        {"username": "bob", "age": 34}
    ]
}
""",
                "response": """
{
    "success": true,
    "inserted_ids": ["60c72b2f9b1d8b1a2d3e4567", "60c72b2f9b1d8b1a2d3e4568"]
}
"""
            },
            {
                "method": "GET",
                "params": {
                    "database_id": "507f1f77bcf86cd799439011",
                    "collection_name": "users",
                    "filters": "{\"age\": {\"$gt\": 30}}",
                    "page": "1",
                    "page_size": "50"
                },
                "response": """
{
    "success": true,
    "data": [
        {"_id": "60c72b2f9b1d8b1a2d3e4568", "username": "bob", "age": 34}
    ],
    "pagination": {
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1
    }
}
"""
            },
            {
                "method": "PUT",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "users",
    "filters": {"username": "alice"},
    "update_data": {"age": 29}
}
""",
                "response": """
{
    "success": true,
    "modified_count": 1
}
"""
            },
            {
                "method": "DELETE",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "users",
    "filters": {"age": {"$lt": 20}},
    "soft_delete": false
}
""",
                "response": """
{
    "success": true,
    "count": 2
}
"""
            }
        ]
    },
    {
        "name": "Import JSON Data",
        "description": "Bulk import JSON via file or raw payload. Auto-creates collection if needed.",
        "url": reverse("api:import_data"),
        "methods": [
            {
                "method": "POST",
                "body": """
{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "events",  # optional
    "json_file": <uploaded JSON file>
}
""",
                "response": """
{
    "success": true,
    "collection": "events",
    "inserted_count": 125
}
"""
            }
        ]
    }
]



# from django.urls import reverse

# apis = [
#     {
#         "name": "Health Check",
#         "description": "Verify that the API server is up and responding.",
#         "url": reverse("api:health_check"),
#         "methods": [
#             {
#                 "method": "GET",
#                 "params": None,
#                 "body": None,
#                 "response": """
# {
#     "success": true,
#     "message": "Server is up"
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "Create Database",
#         "description": "Create a new logical database and its initial collections/fields.",
#         "url": reverse("api:create_database"),
#         "methods": [
#             {
#                 "method": "POST",
#                 "body": """
# {
#     "db_name": "new_database",
#     "collections": [
#         {
#             "name": "users",
#             "fields": [
#                 {"name": "username", "type": "string"},
#                 {"name": "age",      "type": "number"}
#             ]
#         }
#     ]
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "message": "Database 'new_database' and collections created successfully.",
#     "database": {
#         "id": "507f1f77bcf86cd799439011",
#         "name": "new_database"
#     },
#     "collections": [
#         {
#             "name": "users",
#             "id": "607e1c72e13c2a3f4a9b1234",
#             "fields": [
#                 {"name": "username", "type": "string"},
#                 {"name": "age",      "type": "number"}
#             ]
#         }
#     ]
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "Add Collections",
#         "description": "Add one or more new collections (with field definitions) to an existing database.",
#         "url": reverse("api:add_collection"),
#         "methods": [
#             {
#                 "method": "POST",
#                 "body": """
# {
#     "database_id": "507f1f77bcf86cd799439011",
#     "collections": [
#         {
#             "name": "orders",
#             "fields": [
#                 {"name": "order_id", "type": "string"},
#                 {"name": "total",    "type": "number"}
#             ]
#         }
#     ]
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "message": "Collections 'orders' created successfully.",
#     "collections": [
#         {
#             "name": "orders",
#             "id": "607e1e33a1b2c4d5e6f78901",
#             "fields": [
#                 {"name": "order_id", "type": "string"},
#                 {"name": "total",    "type": "number"}
#             ]
#         }
#     ],
#     "database": {
#         "total_collections": 2,
#         "total_fields": 4
#     }
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "List Databases",
#         "description": "Page through all databases, with optional MongoDB‐style filter, and get real‐time collection counts.",
#         "url": reverse("api:list_databases"),
#         "methods": [
#             {
#                 "method": "POST",
#                 "body": """
# {
#     "page": 1,
#     "page_size": 10,
#     "filter": {
#         "number_of_collections": { "$gte": 2 },
#         "database_name": { "$regex": "^prod_" }
#     }
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "data": [
#         {"id": "507f1f77bcf86cd799439011", "database_name": "prod_users", "num_collections": 5},
#         {"id": "507f1f77bcf86cd799439012", "database_name": "prod_orders","num_collections": 3}
#     ],
#     "pagination": {
#         "page": 1,
#         "page_size": 10,
#         "total": 2,
#         "total_pages": 1
#     }
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "List Collections",
#         "description": "Retrieve all collections in a given database, with document counts per collection.",
#         "url": reverse("api:list_collections"),
#         "methods": [
#             {
#                 "method": "GET",
#                 "params": {
#                     "database_id": "507f1f77bcf86cd799439011"
#                 },
#                 "response": """
# {
#     "success": true,
#     "collections": [
#         {"name": "users", "num_documents": 42},
#         {"name": "orders","num_documents": 128}
#     ]
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "Get Database Metadata",
#         "description": "Fetch the stored metadata document for a database, including all collections and field details.",
#         "url": reverse("api:get_metadata"),
#         "methods": [
#             {
#                 "method": "GET",
#                 "params": {
#                     "database_id": "507f1f77bcf86cd799439011"
#                 },
#                 "response": """
# {
#     "success": true,
#     "data": {
#         "_id": "507f1f77bcf86cd799439011",
#         "database_name": "example_db",
#         "number_of_collections": 2,
#         "number_of_fields": 5,
#         "collections": [
#             {
#                 "name": "users",
#                 "fields": [
#                     {"name": "username", "type": "string"},
#                     {"name": "email",    "type": "string"}
#                 ]
#             },
#             {
#                 "name": "orders",
#                 "fields": [
#                     {"name": "order_id", "type": "string"},
#                     {"name": "total",    "type": "number"}
#                 ]
#             }
#         ]
#     }
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "Drop Database",
#         "description": "Permanently delete a database's metadata and all its collections (requires name confirmation).",
#         "url": reverse("api:drop_database"),
#         "methods": [
#             {
#                 "method": "DELETE",
#                 "body": """
# {
#     "database_id":  "507f1f77bcf86cd799439011",
#     "confirmation": "example_db"
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "message": "Database 'example_db' and its metadata dropped successfully"
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "Drop Collections",
#         "description": "Remove one or more collections from an existing database (updates metadata and drops actual collections).",
#         "url": reverse("api:drop_collections"),
#         "methods": [
#             {
#                 "method": "DELETE",
#                 "body": """
# {
#     "database_id":     "507f1f77bcf86cd799439011",
#     "collection_names":["users","orders"]
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "dropped_collections": ["users","orders"],
#     "failed_collections":  []
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "CRUD Documents",
#         "description": "Create, read, update, and delete documents in a specific collection using full MongoDB filters.",
#         "url": reverse("api:crud"),
#         "methods": [
#             {
#                 "method": "POST",
#                 "body": """
# {
#     "database_id":     "507f1f77bcf86cd799439011",
#     "collection_name": "users",
#     "data": [
#         {"username": "alice", "age": 28},
#         {"username": "bob",   "age": 34}
#     ]
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "inserted_ids": ["60c72b2f9b1d8b1a2d3e4567", "60c72b2f9b1d8b1a2d3e4568"]
# }
# """,
#             },
#             {
#                 "method": "GET",
#                 "params": {
#                     "database_id":     "507f1f77bcf86cd799439011",
#                     "collection_name": "users",
#                     "filters":         "{\"age\":{\"$gt\":30}}",
#                     "page":            "1",
#                     "page_size":       "50"
#                 },
#                 "response": """
# {
#     "success": true,
#     "data": [
#         {"_id":"60c72b2f9b1d8b1a2d3e4568","username":"bob","age":34}
#     ],
#     "pagination": {
#         "page": 1,
#         "page_size": 50,
#         "total": 1,
#         "total_pages": 1
#     }
# }
# """,
#             },
#             {
#                 "method": "PUT",
#                 "body": """
# {
#     "database_id":     "507f1f77bcf86cd799439011",
#     "collection_name": "users",
#     "filters":         {"username":"alice"},
#     "update_data":     {"age":29}
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "modified_count": 1
# }
# """,
#             },
#             {
#                 "method": "DELETE",
#                 "body": """
# {
#     "database_id":     "507f1f77bcf86cd799439011",
#     "collection_name": "users",
#     "filters":         {"age": {"$lt":20}},
#     "soft_delete":     false
# }
# """,
#                 "response": """
# {
#     "success": true,
#     "count":  2
# }
# """,
#             }
#         ],
#     },
#     {
#         "name": "Import JSON Data",
#         "description": "Bulk-import JSON (file or payload) into a collection.  If the collection does not yet exist, it will be auto-created (with fields inferred).",
#         "url": reverse("api:import_data"),
#         "methods": [
#             {
#                 "method": "POST",
#                 "body": """
# {
#     "database_id":     "507f1f77bcf86cd799439011",
#     "collection_name": "events",      # optional
#     "json_file":       <uploaded JSON file>
# }
# """,
#                 "response": """
# {
#     "success":        true,
#     "collection":     "events",
#     "inserted_count": 125
# }
# """,
#             }
#         ],
#     },
# ]