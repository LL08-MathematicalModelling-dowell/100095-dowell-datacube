"""
API serializers for MongoDB database operations.

This module contains all serializers used by the API, organized by functionality.
"""

import re
from rest_framework import serializers
from api.domain.metadata_models import FIELD_TYPE_CHOICES, normalize_field_type
from api.infrastructure.query_safety import MAX_BULK_UPDATE_OPERATIONS
from api.infrastructure.validators import validate_collection_name, validate_unique_fields


class ObjectIdField(serializers.CharField):
    """
    Custom serializer field to validate a string as a valid MongoDB ObjectId.
    """
    def to_internal_value(self, data):
        if not isinstance(data, str) or not re.match(r'^[a-fA-F0-9]{24}$', data):
            raise serializers.ValidationError(
                "Must be a valid 24-character hexadecimal ObjectId."
            )
        return data

    def to_representation(self, value):
        return str(value)


class FieldSerializer(serializers.Serializer):
    """Serializer for a single field within a collection's schema."""
    
    name = serializers.CharField(
        max_length=100,
        help_text="Name of the field. Use only letters, numbers, underscores (_), or hyphens (-)."
    )
    
    type = serializers.ChoiceField(
        choices=FIELD_TYPE_CHOICES,
        default="string",
        help_text="Type of the field. Defaults to 'string'.",
    )

    def validate_type(self, value):
        return normalize_field_type(value)

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
    
    fields = FieldSerializer(
        many=True, 
        help_text="List of fields defining the collection's schema."
    )

    def validate_name(self, value):
        return validate_collection_name(value)


# ==================== Database Operations ====================

class AddDatabasePOSTSerializer(serializers.Serializer):
    """Validates the request for creating a new database."""
    
    db_name = serializers.CharField(
        max_length=100,
        help_text="Name of the new database. Must be unique for the user."
    )
    
    collections = CollectionSerializer(
        many=True, 
        min_length=1,
        max_length=500,
        help_text="List of collections to create within the database."
    )

    def validate_db_name(self, value):
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError(
                "Database name can only contain alphanumeric characters, underscores, or hyphens."
            )
        if value.lower() in {"admin", "local", "config"}:
            raise serializers.ValidationError(
                f"The database name '{value}' is reserved and cannot be used."
            )
        return value

    def validate_collections(self, value):
        validate_unique_fields(value)
        # ensure maximum collections is 500
        if len(value) > 500:
            raise serializers.ValidationError(
                "A maximum of 500 collections can be created in a single api request."
            )
        return value


class AddCollectionPOSTSerializer(serializers.Serializer):
    """Validates the request for adding collections to an existing database."""
    
    database_id = ObjectIdField(
        help_text="ID of the existing database to add collections to."
    )
    
    collections = CollectionSerializer(
        many=True, 
        help_text="List of collections to add to the database."
    )

    def validate_collections(self, value):
        validate_unique_fields(value)
        return value


# ==================== Document Operations ====================

class DocumentBaseSerializer(serializers.Serializer):
    """Base serializer for document operations."""
    
    database_id = ObjectIdField(
        help_text="The ID of the target database."
    )
    
    collection_name = serializers.CharField(
        max_length=100,
        help_text="The name of the target collection."
    )


class AsyncPostDocumentSerializer(DocumentBaseSerializer):
    """Validates the request for creating new documents."""
    
    documents = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=500,
        help_text="One to 500 documents (JSON objects) to insert per request.",
    )


class UpdateDocumentSerializer(DocumentBaseSerializer):
    """Validates the request for updating documents."""
    
    filters = serializers.JSONField(
        help_text="MongoDB query; must be non-empty. Single-doc updates require _id or id."
    )
    
    update_data = serializers.JSONField(
        help_text="Plain field map or allowed update operators ($set, $inc, …)."
    )
    
    update_all_fields = serializers.BooleanField(
        default=False,
        help_text=(
            "If true, apply update_data with $set/operators (may add new fields). "
            "If false, only change fields that already exist on each document."
        ),
    )

    update_many = serializers.BooleanField(
        default=False,
        help_text="If true, update all documents matching filters; otherwise update one.",
    )

    upsert = serializers.BooleanField(
        default=False,
        help_text="If true and filters include _id/id, insert when no document matches (single update only).",
    )

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        if not value:
            raise serializers.ValidationError("filters must not be empty.")
        return value

    def validate_update_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Update data must be a valid JSON object/dictionary.")
        if not value:
            raise serializers.ValidationError("update_data must not be empty.")
        return value

    def validate(self, attrs):
        filters = attrs.get("filters") or {}
        upsert = attrs.get("upsert", False)
        update_many = attrs.get("update_many", False)

        if upsert and update_many:
            raise serializers.ValidationError(
                {"upsert": "Cannot combine upsert with update_many."}
            )
        if upsert and "_id" not in filters and "id" not in filters:
            raise serializers.ValidationError(
                {"upsert": "Requires _id or id in filters."}
            )
        if not update_many and "_id" not in filters and "id" not in filters:
            raise serializers.ValidationError(
                {
                    "filters": (
                        "Single-document update requires _id or id in filters, "
                        "or set update_many to true."
                    )
                }
            )
        return attrs


class BulkUpdateOperationSerializer(serializers.Serializer):
    """One updateOne operation inside a bulk CRUD request."""

    filters = serializers.JSONField(
        help_text="MongoDB query; must be non-empty and include _id or id."
    )
    update_data = serializers.JSONField(
        help_text="Plain field map or allowed update operators ($set, $inc, …)."
    )
    update_all_fields = serializers.BooleanField(
        default=False,
        help_text=(
            "If true, apply update_data with $set/operators (may add new fields). "
            "Required when upsert is true."
        ),
    )
    upsert = serializers.BooleanField(
        default=False,
        help_text="If true, insert when no active document matches (requires _id/id).",
    )

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        if not value:
            raise serializers.ValidationError("filters must not be empty.")
        return value

    def validate_update_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Update data must be a valid JSON object/dictionary.")
        if not value:
            raise serializers.ValidationError("update_data must not be empty.")
        return value

    def validate(self, attrs):
        filters = attrs.get("filters") or {}
        upsert = attrs.get("upsert", False)
        update_all_fields = attrs.get("update_all_fields", False)

        if "_id" not in filters and "id" not in filters:
            raise serializers.ValidationError(
                {"filters": "Each operation requires _id or id in filters."}
            )
        if upsert and not update_all_fields:
            raise serializers.ValidationError(
                {"upsert": "Requires update_all_fields=true."}
            )
        return attrs


class BulkUpdateDocumentSerializer(DocumentBaseSerializer):
    """Validates a batch of per-document update/upsert operations."""

    operations = BulkUpdateOperationSerializer(
        many=True,
        min_length=1,
        max_length=MAX_BULK_UPDATE_OPERATIONS,
        help_text="One to 500 independent updateOne operations (optional upsert per row).",
    )


class DeleteDocumentSerializer(DocumentBaseSerializer):
    """Validates the request for deleting documents."""
    
    filters = serializers.JSONField(
        help_text="A MongoDB query object to select which documents to delete."
    )
    
    soft_delete = serializers.BooleanField(
        default=True,
        help_text="If true, sets 'is_deleted: true'. If false, permanently removes documents."
    )

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        if not value:
            raise serializers.ValidationError("filters must not be empty.")
        return value


class DocumentQuerySerializer(DocumentBaseSerializer):
    """Serializer for validating and sanitizing MongoDB document query parameters."""
    
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
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        return value


class ListQuerySerializer(serializers.Serializer):
    """Serializer for list operations with pagination and filtering."""
    
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
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be a valid JSON object/dictionary.")
        return value


# ==================== Import/Export Operations ====================

class JsonImportSerializer(DocumentBaseSerializer):
    """Validates the request for importing data from a JSON file."""
    
    json_file = serializers.FileField(
        help_text="The .json file to upload."
    )
    
    collection_name = serializers.CharField(
        required=False,
        help_text="Optional: name of the collection. If omitted, it's derived from the filename."
    )


# ==================== Drop Operations ====================

class DatabaseDropSerializer(serializers.Serializer):
    """Serializer for dropping a database."""
    
    database_id = ObjectIdField(
        required=True,
        help_text="ID of the database to drop."
    )
    
    confirmation = serializers.CharField(
        required=True,
        help_text="Confirmation string to prevent accidental deletion."
    )


class CollectionDropSerializer(serializers.Serializer):
    """Serializer for dropping collections from a database."""
    
    database_id = ObjectIdField(
        required=True,
        help_text="ID of the database containing the collections."
    )
    
    collection_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        required=True,
        help_text="List of collection names to drop."
    )