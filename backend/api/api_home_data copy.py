from django.urls import reverse


apis = [
        {
            "name": "Data CRUD",
            "description": "Handles CRUD operations on MongoDB collections.",
            "url": reverse('api:crud'),
            "request_bodies": {
                "GET": """{
                    "db_name": "example_db",
                    "coll_name": "example_collection",
                    "filters": {"field": "value"},
                    "limit": 50,
                    "offset": 0,
                    "is_deleted": false
                }""",
                "POST": """{
                    "db_name": "example_db",
                    "coll_name": "example_collection",
                    "data": {
                        "field1": "value1",
                        "field2": "value2"
                    }
                }""",
                "PUT": """{
                    "db_name": "example_db",
                    "coll_name": "example_collection",
                    "operation": "update",
                    "query": {"field": "value"},
                    "update_data": {"field1": "new_value"}
                }""",
                "DELETE": """{
                    "db_name": "example_db",
                    "coll_name": "example_collection",
                    "operation": "soft_delete",
                    "query": {"field": "value"}
                }"""
            },
            "responses": {
                "GET": """{
                    "success": true,
                    "message": "Data found!",
                    "data": [...]
                }""",
                "POST": """{
                    "success": true,
                    "message": "Documents inserted successfully!"
                }""",
                "PUT": """{
                    "success": true,
                    "message": "Document updated successfully"
                }""",
                "DELETE (soft_delete)": """{
                    "success": true,
                    "message": "Document soft-deleted successfully"
                }""",
                "DELETE (hard delete)": """{
                    "success": true,
                    "message": "Document deleted successfully"
                }"""
            }
        },
        {
            "name": "List Collections",
            "description": "Lists all collections for a specified database.",
            "url": reverse('api:list_collections'),
            "request_bodies": {
                "GET": """{
                    "db_name": "example_db"
                }"""
            },
            "responses": {
                "GET": """{
                    "success": true,
                    "message": "Collections retrieved successfully",
                    "data": ["collection1", "collection2", ...]
                }"""
            }
        },
        {
            "name": "Add Collection",
            "description": "Adds new collections to an existing database, specifying document fields for each collection.",
            "url": reverse('api:add_collection'),
            "request_bodies": {
                "POST": """{
                    "db_name": "example_db",
                    "collections": [
                        {
                            "name": "new_collection",
                            "fields": ["field1", "field2", "field3"]
                        },
                        {
                            "name": "another_collection",
                            "fields": ["fieldA", "fieldB", "fieldC"]
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
            "name": "Create Database",
            "description": "Creates a new database with specified collections and fields.",
            "url": reverse('api:create_database'),
            "request_bodies": {
                "POST": """{
                    "db_name": "new_database",
                    "collections":  [
                        {
                            "name": "collection1",
                            "fields": ["field1", "field2", "field3"]
                        },
                        {
                            "name": "collection2",
                            "fields": ["fieldA", "fieldB", "fieldC"]
                        }
                    ]
                }"""
            },
            "responses": {
                "POST": """{
                    "success": true,
                    "message": "Database created successfully"
                }"""
            }
        },
        {
            "name": "List Databases",
            "description": "Lists all databases in the MongoDB cluster with pagination and optional filtering.",
            "url": reverse('api:list_databases'),
            "request_bodies": {
                "GET": """{
                    "page": 1,
                    "page_size": 10,
                    "filter": "example"
                }"""
            },
            "responses": {
                "GET": """{
                    "success": true,
                    "message": "Databases retrieved successfully"
                }"""
            }
        },
        {
            "name": "Get Metadata",
            "description": "Fetches metadata for a specific database, including collections, fields, and additional metadata.",
            "url": reverse('api:get_metadata'),
            "request_bodies": {
                "GET": """{
                    "db_name": "example_db"
                }"""
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
        },
        # {
        #     "name": "Drop Database",
        #     "description": "Deletes a database and all its collections and metadata with confirmation.",
        #     "url": reverse('api:drop_database'),
        #     "request_bodies": {
        #         "DELETE": """{
        #             "db_name": "example_db",
        #             "confirmation": "example_db"
        #         }"""
        #     },
        #     "responses": {
        #         "DELETE": """{
        #             "success": true,
        #             "message": "Database dropped successfully"
        #         }"""
        #     }
        # }
    ]



