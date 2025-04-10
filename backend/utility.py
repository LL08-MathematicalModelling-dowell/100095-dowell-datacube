"""Utility module containing metadata schema and helper functions."""

METADATA_SCHEMA = {
    "_id": "UUID",  # database primary key
    "database_name": "your_database_name",
    "created_at": "ISODate",  # Timestamp for creation
    "collections": [
        {
            "name": "collection_name",
            "created_at": "ISODate",  # Timestamp for collection creation
            "fields": [
                {
                    "name": "field_name",
                    "type": "string",  # or "number", "boolean", "date", "objectId", etc.
                    "required": True,   # Optional: Define if a field is mandatory
                    "unique": False,    # Optional: Define if field should be unique
                    "indexed": True     # Optional: Define if a field is indexed
                 }
             ]
         }
    ],
    "number_of_collections": "Number",
    "user_id": "UUID"  # Reference to user model
}

