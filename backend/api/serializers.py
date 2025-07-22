"""
This file contains all serializers used by the API.

It has been cleaned up to remove unused serializers and consolidate logic
based on the current, secure implementation of the API views.
"""

import re
from rest_framework import serializers
from bson import ObjectId


# --- Reusable Custom Fields & Base Serializers ---

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
            "null", "binary", "objectid", "decimal128", "regex", "timestamp"
        ],
        default="string",
        help_text="Type of the field. Defaults to 'string'."
    )

    def validate_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Field name can only contain alphanumeric characters, underscores, or hyphens.")
        return value


class CollectionSerializer(serializers.Serializer):
    """Serializer for a collection's name and its schema of fields."""
    name = serializers.CharField(
        max_length=100,
        help_text="Name of the collection. Use only letters, numbers, underscores (_), or hyphens (-)."
    )
    fields = serializers.ListField(
        child=FieldSerializer(),
        min_length=1,
        help_text="List of fields with names and optional types for the collection."
    )

    def validate_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Collection name can only contain alphanumeric characters, underscores, or hyphens.")
        return value


class AddDatabasePOSTSerializer(serializers.Serializer):
    """Validates the request for creating a new database."""
    db_name = serializers.CharField(
        max_length=100,
        help_text="Name of the new database. Must be unique for the user."
    )
    collections = serializers.ListField(
        child=CollectionSerializer(),
        min_length=1,
        help_text="A list of at least one collection to create within the new database."
    )

    def validate_db_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
        if value.lower() in ["admin", "local", "config"]:
            raise serializers.ValidationError(f"The database name '{value}' is reserved and cannot be used.")
        return value


class AddCollectionPOSTSerializer(serializers.Serializer):
    """Validates the request for adding collections to an existing database."""
    database_id = ObjectIdField(help_text="ID of the existing database to add collections to.")
    collections = serializers.ListField(
        child=CollectionSerializer(),
        min_length=1,
        help_text="A list of at least one new collection to add."
    )


# --- Data CRUD Operation Serializers ---

class AsyncPostDocumentSerializer(serializers.Serializer):
    """Validates the request for creating new documents."""
    database_id = ObjectIdField(help_text="The ID of the target database.")
    collection_name = serializers.CharField(max_length=100, help_text="The name of the target collection.")
    data = serializers.ListField(
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
    update_all_fields = serializers.BooleanField(default=False, help_text="Set to true to use $set, otherwise only existing fields are updated.")


class DeleteDocumentSerializer(serializers.Serializer):
    """Validates the request for deleting documents."""
    database_id = ObjectIdField(help_text="The ID of the target database.")
    collection_name = serializers.CharField(max_length=100, help_text="The name of the target collection.")
    filters = serializers.JSONField(help_text="A MongoDB query object to select which documents to delete.")
    soft_delete = serializers.BooleanField(default=True, help_text="If true, sets 'is_deleted: true'. If false, permanently removes documents.")


# --- Utility Serializers ---

class JSonImportSerializer(serializers.Serializer):
    """Validates the request for importing data from a JSON file."""
    database_id = ObjectIdField(help_text="The ID of the database to import data into.")
    collection_name = serializers.CharField(required=False, help_text="Optional: name of the collection. If omitted, it's derived from the filename.")
    json_file = serializers.FileField(help_text="The .json file to upload.")