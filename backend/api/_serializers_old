"""
This file contains all serializers used by the API.

It has been cleaned up to remove unused serializers and consolidate logic
based on the current, secure implementation of the API views.
"""

import re
from rest_framework import serializers
from api.utils.validators import validate_collection_name, validate_unique_fields


class ObjectIdField(serializers.CharField):
    """
    Custom serializer field to validate a string as a valid MongoDB ObjectId.
    """
    def to_internal_value(self, data):
        # First, validate the format to provide a clear error message.
        if not isinstance(data, str) or not re.match(r'^[a-fA-F0-9]{24}$', data):
            raise serializers.ValidationError("Must be a valid 24-character hexadecimal ObjectId.")
        # If format is valid, it can be used directly in services that call ObjectId().
        return data


# --- Database & Collection Structure Serializers ---

class FieldSerializer(serializers.Serializer):
    """Serializer for a single field within a collection's schema."""
    name = serializers.CharField(
        max_length=100,
        help_text="Name of the field. Use only letters, numbers, underscores (_), or hyphens (-)."
    )
    type = serializers.ChoiceField(
        choices=[
            "string", "number", "object", "array", "boolean", "date", "datetime",
            "null", "binary", "objectid", "decimal128", "regex", "timestamp", "int",
            "long", "double","float",
        ],
        default="string",
        help_text="Type of the field. Defaults to 'string'."
    )

    def validate_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError(
                "Field name can only contain alphanumeric characters, underscores, or hyphens."
            )
        return value


class CollectionSerializer(serializers.Serializer):
    """Serializer for a collection's name and its schema of fields."""
    name = serializers.CharField(
        max_length=100,
        help_text="Name of the collection. Use only letters, numbers, underscores (_), or hyphens (-)."
    )
    fields = FieldSerializer(many=True, help_text="List of fields defining the collection's schema.") # type: ignore
    
    def validate_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError(
                "Collection name can only contain alphanumeric characters, underscores, or hyphens."
            )
        return value


# class AddDatabasePOSTSerializer(serializers.Serializer):
#     """Validates the request for creating a new database."""
#     db_name = serializers.CharField(
#         max_length=100,
#         help_text="Name of the new database. Must be unique for the user."
#     )
#     collections = serializers.ListField(
#         child=CollectionSerializer(),
#         min_length=1,
#         help_text="A list of at least one collection to create within the new database."
#     )

#     def validate_db_name(self, value):
#         if not re.match(r'^[\w-]+$', value):
#             raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
#         if value.lower() in ["admin", "local", "config"]:
#             raise serializers.ValidationError(f"The database name '{value}' is reserved and cannot be used.")
#         return value


class AddCollectionPOSTSerializer(serializers.Serializer):
    """Validates the request for adding collections to an existing database."""
    database_id = ObjectIdField(help_text="ID of the existing database to add collections to.")
    collections = CollectionSerializer(many=True, help_text="List of collections to add to the database.")


class AsyncPostDocumentSerializer(serializers.Serializer):
    """Validates the request for creating new documents."""
    database_id = ObjectIdField(help_text="The ID of the target database.")
    collection_name = serializers.CharField(max_length=100, help_text="The name of the target collection.")
    documents = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text="A list containing one or more documents (as JSON objects) to insert."
    )


class UpdateDocumentSerializer(serializers.Serializer):
    """Validates the request for updating documents."""
    database_id = ObjectIdField(help_text="The ID of the target database.")
    collection_name = serializers.CharField(max_length=100, help_text="The name of the target collection.")
    filters = serializers.JSONField(help_text="A MongoDB query object to select which documents to update.")
    update_data = serializers.JSONField(help_text="A MongoDB update object (e.g., using $set).")
    update_all_fields = serializers.BooleanField(
        default=False, # type: ignore
        help_text="Set to true to use $set, otherwise only existing fields are updated."
    )


class DeleteDocumentSerializer(serializers.Serializer):
    """Validates the request for deleting documents."""
    database_id = ObjectIdField(help_text="The ID of the target database.")
    collection_name = serializers.CharField(max_length=100, help_text="The name of the target collection.")
    filters = serializers.JSONField(help_text="A MongoDB query object to select which documents to delete.")
    soft_delete = serializers.BooleanField(
        default=True, # type: ignore
        help_text="If true, sets 'is_deleted: true'. If false, permanently removes documents."
    )


# --- Utility Serializers ---

class JSonImportSerializer(serializers.Serializer):
    """Validates the request for importing data from a JSON file."""
    database_id = ObjectIdField(help_text="The ID of the database to import data into.")
    collection_name = serializers.CharField(
        required=False,
        help_text="Optional: name of the collection. If omitted, it's derived from the filename."
    )
    json_file = serializers.FileField(help_text="The .json file to upload.")


class CollectionFieldSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    type = serializers.CharField(default="string")

class CollectionSchemaSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    fields = CollectionFieldSerializer(many=True) # type: ignore

    def validate_name(self, value):
        validate_collection_name(value)
        return value

    def validate_fields(self, value):
        validate_unique_fields(value)
        return value

class AddDatabasePOSTSerializer(serializers.Serializer):
    db_name = serializers.CharField(max_length=100)
    collections = CollectionSchemaSerializer(many=True, min_length=1)

    def validate_db_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
        if value.lower() in ["admin", "local", "config"]:
            raise serializers.ValidationError(f"The database name '{value}' is reserved and cannot be used.")
        return value
class DocumentQuerySerializer(serializers.Serializer):
    """
    Serializer for validating and sanitizing MongoDB document query parameters.
    Used primarily in GET requests for pagination and filtering.
    """
    
    # Required parameters for locating the data
    database_id = serializers.CharField(
        required=True, 
        help_text="The unique ID of the target database."
    )
    collection_name = serializers.CharField(
        required=True, 
        help_text="The name of the MongoDB collection to query."
    )
    
    # Optional filtering parameter
    # 2025 Note: Using JSONField allows passing complex Mongo queries like {'age': {'$gt': 20}}
    filters = serializers.JSONField(
        required=False, 
        default=dict,
        help_text="A JSON object containing MongoDB query filters."
    )
    
    # Pagination parameters with sane 2025 defaults
    page = serializers.IntegerField(
        required=False, 
        default=1, 
        min_value=1,
        help_text="The page number to retrieve (starts at 1)."
    )
    page_size = serializers.IntegerField(
        required=False, 
        default=50, 
        min_value=1, 
        max_value=1000,
        help_text="Number of documents to return per page. Max 1000."
    )

    def validate_filters(self, value):
        """
        Custom validation to ensure filters are a dictionary.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        return value

    def validate(self, attrs):
        """
        Cross-field validation if necessary (e.g., ensuring certain collections 
        always require specific filters).
        """
        return attrs

class ListQuerySerializer(serializers.Serializer):
    filters = serializers.JSONField(
        required=False, 
        default=dict,
        help_text="A JSON object containing MongoDB query filters."
    )    
    page = serializers.IntegerField(
        required=False, 
        default=1, 
        min_value=1,
        help_text="The page number to retrieve (starts at 1)."
    )
    page_size = serializers.IntegerField(
        required=False, 
        default=50, 
        min_value=1, 
        max_value=1000,
        help_text="Number of documents to return per page. Max 1000."
    )

    def validate_filters(self, value):
        """
        Custom validation to ensure filters are a dictionary.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        return value

class DatabaseDropSerializer(serializers.Serializer):
    database_id = serializers.CharField(required=True)
    confirmation = serializers.CharField(required=True)

class CollectionDropSerializer(serializers.Serializer):
    database_id = serializers.CharField(required=True)
    collection_names = serializers.ListField(
        child=serializers.CharField(), 
        min_length=1, 
        required=True
    )
