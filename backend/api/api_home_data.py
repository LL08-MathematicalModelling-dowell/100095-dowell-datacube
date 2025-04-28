from django.urls import reverse

apis = [
{
"name": "Health Check",
"description": "Checks the health status of the API.",
"url": reverse('api:health_check'),
"request_bodies": {
"GET": "{}"  # No body needed for health check
},
"responses": {
"GET": """{
    "success": true,
    "message": "API is healthy"
}"""
}
},
{
"name": "Create Database",
"description": "Creates a new database with specified collections and fields.",
"url": reverse('api:create_database'),
"request_bodies": {
"POST": """{
    "db_name": "new_database",
    "collections":  [
        {
            "name": "users",
            "fields": [
                {"name": "username", "type": "string"},
                {"name": "age", "type": "number"}
            ]
        }
    ]
}"""
},
"responses": {
"POST": """{
    "success": true,
    "message": "Database created successfully"
}"""
},
},
{
"name": "Add Collections",
"description": "Adds new collections to an existing database, specifying document fields for each collection.",
"url": reverse('api:add_collection'),
"request_bodies": {
"POST": """{
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
}"""
},
"responses": {
"POST": """{
    "success": true,
    "message": "Collections added successfully"
}"""
}
},
{
"name": "List Collections",
"description": "Lists all collections in a specified database.",
"url": reverse('api:list_collections'),
"request_params": {
"database_id": "507f1f77bcf86cd799439011"
},
"responses": {
"GET": """{
    "success": true,
    "message": "Collections retrieved successfully",
    "data": [
        "users",
        "products"
    ]
}"""
}
},
{
"name": "Create Documents",
"description": "Creates documents in a specified collection.",
"url": reverse('api:crud'),
"request_bodies": {
"POST": """{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "users",
    "data": [
        {
            "username": "john_doe",
            "age": 30
        }
    ]
}"""
},
"responses": {
"POST": """{
    "success": true,
    "message": "Documents inserted successfully!"
}"""
}
},
{
"name": "Read Documents",
"description": "Reads documents from a specified collection with optional filters.",
"url": reverse('api:crud'),
"request_params": {
"database_id": "507f1f77bcf86cd799439011",
"collection_name": "users",
"filters": "{\"age\":{\"$gt\":25}}",
"limit": 50,
"offset": 0
},
"responses": {
"GET": """{
    "success": true,
    "message": "Data found!",
    "data": [...]
}"""
}
},
{
"name": "Update Documents",
"description": "Updates documents in a specified collection.",
"url": reverse('api:crud'),
"request_bodies": {
"PUT": """{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "users",
    "filters": {"username": "john_doe"},
    "update_data": {"age": 31}
}"""
},
"responses": {
"PUT": """{
    "success": true,
    "message": "Document updated successfully"
}"""
}
},
{
"name": "Delete Documents",
"description": "Deletes documents from a specified collection.",
"url": reverse('api:crud'),
"request_bodies": {
"DELETE": """{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_name": "users",
    "filters": {"username": "john_doe"},
    "soft_delete": true
}"""
},
"responses": {
"DELETE": """{
    "success": true,
    "message": "Document deleted successfully"
}"""
}
},

{
"name": "List Databases",
"description": "Lists all databases in the MongoDB cluster with pagination and optional filtering.",
"url": reverse('api:list_databases'),
"request_params": {
"page": 1,
"page_size": 10,
"filter": "example"
},
"responses": {
"GET": """{
    "success": true,
    "message": "Databases retrieved successfully",
    "data": [
        {
      "name": "example_db",
      "num_collections": 3
    },
    {
      "name": "user_data_db",
      "num_collections": 1
    },
  ]
}"""
},
"list_collections": """{
"databases": [
    {
        "database_id": "507f1f77bcf86cd799439011",
        "name": "example_db"
    }
]
}"""
},
{
"name": "Drop Database",
"description": "Deletes a database and all its collections and metadata with confirmation.",
"url": reverse('api:drop_database'),
"request_bodies": {
"DELETE": """{
    "database_id": "507f1f77bcf86cd799439011",
    "confirmation": "example_db"
}"""
},
"responses": {
"DELETE": """{
    "success": true,
    "message": "Database dropped successfully"
}"""
}
},
{
"name": "Drop Collections",
"description": "Deletes specified collections from a database.",
"url": reverse('api:drop_collections'),
"request_bodies": {
"DELETE": """{
    "database_id": "507f1f77bcf86cd799439011",
    "collection_names": ["users", "orders"]
}"""
},
"responses": {
"DELETE": """{
    "success": true,
    "message": "Collections dropped successfully"
}"""
}
},
{
"name": "Get Database Metadata",
"description": "Fetches metadata for a specific database, including collections, fields, and additional metadata.",
"url": reverse('api:get_metadata'),
"request_params": {
"database_id": "507f1f77bcf86cd799439011"
},
"responses": {
"GET": """{
    "success": true,
    "message": "Metadata retrieved successfully",
    "data": {
        "database_name": "example_db",
        "number_of_collections": 3,
        "number_of_fields": 12,
        "collections_metadata": [...]
    }
}"""
}
}
]

