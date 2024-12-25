import re
from django.conf import settings
from rest_framework import serializers


class InputGetSerializer(serializers.Serializer):
    db_name = serializers.CharField(max_length=255, required=True)
    coll_name = serializers.CharField(max_length=255, required=True)
    filters = serializers.JSONField(required=False)
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)


class InputPostSerializer(serializers.Serializer):
    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    data = serializers.JSONField(required=True)

    def validate_data(self, value):
        """
        Ensures `data` is either a dictionary (single document) or a list of dictionaries (multiple documents).
        """
        if isinstance(value, dict):
            # Single document case
            return [value]  # Wrap in a list for uniform handling in the view
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            # Multiple documents case
            return value
        else:
            raise serializers.ValidationError("The `data` field must be a dictionary or a list of dictionaries representing documents to insert.")



class InputPutSerializer(serializers.Serializer):
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.ChoiceField(choices=['update', 'replace'])
    query = serializers.JSONField(required=True)
    update_data = serializers.JSONField(required=True)

    def validate(self, data):
        # Ensure `update_data` is present if `operation` is 'update'
        if data['operation'] == 'update' and not data.get('update_data'):
            raise serializers.ValidationError("`update_data` is required for update operations.")
        return data


class InputDeleteSerializer(serializers.Serializer):
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.ChoiceField(choices=['delete', 'soft_delete'])
    query = serializers.JSONField(required=True)

    def validate(self, data):
        # Ensure that `query` is provided
        if not data.get('query'):
            raise serializers.ValidationError("A `query` is required to specify the document(s) to delete.")
        return data


class NotEmptyStringValidator:
    def __call__(self, value):
        if value == "":
            raise serializers.ValidationError("This field cannot be empty.")


class NoSpecialCharsValidator:
    def __call__(self, value):
        for char in value:
            if not char.isalnum() and char != ',' and char != '_': # Added '_' to allowed characters
                raise serializers.ValidationError("This field cannot contain special characters except commas and underscores.")


class NoSpacesValidator:
    def __call__(self, value):
        if ' ' in value.strip():
            raise serializers.ValidationError("This field cannot contain spaces.")


class GetCollectionsSerializer(serializers.Serializer):
    # api_key = serializers.CharField(max_length=510, required=True)
    db_name = serializers.CharField(max_length=100)
    # payment = serializers.BooleanField(default=True, allow_null=True, required=False)


class DropDatabaseSerializer(serializers.Serializer):
    """
    Serializer class to validate the database name and confirmation for dropping a database.
    """
    db_name = serializers.CharField(max_length=100)
    confirmation = serializers.CharField(max_length=100)


class ListDatabaseSerializer(serializers.Serializer):
    page = serializers.IntegerField(default=1)
    page_size = serializers.IntegerField(default=10)
    filter = serializers.CharField(default='')


class AddDatabasePOSTSerializer(serializers.Serializer):
    db_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the new database"
    )
    product_name = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Product name to configure database setup"
    )
    coll_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        # default=[],
        help_text="List of collection names to be created in the database"
    )

    def validate_db_name(self, value):
        """Ensure db_name only contains alphanumeric characters, underscores, or hyphens."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
        return value


# =================== Add Collection ===================


class FieldSerializer(serializers.Serializer):
    MONGODB_FIELD_TYPES = [
    "string",       # Textual data
    "number",       # Numeric data
    "object",       # Embedded document
    "array",        # List of values
    "boolean",      # True/False
    "date",         # ISO 8601 date
    "null",         # Null value
    "binary",       # Binary data
    "objectid",     # ObjectId
    "decimal128",   # High-precision decimal
    "regex",        # Regular expression
    "timestamp"     # Timestamp
    ]

    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the field. Use only letters, numbers, underscores (_), or hyphens (-)."
    )
    type = serializers.ChoiceField(
        choices=MONGODB_FIELD_TYPES,
        required=False,
        help_text="Type of the field. Optional, defaults to 'string'."
    )

    def validate_name(self, value):
        """Validate field name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Field name can only contain alphanumeric characters, underscores, or hyphens.")
        return value


class CollectionSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the collection to be created. Use only letters, numbers, underscores (_), or hyphens (-)."
    )
    fields = serializers.ListField(
        child=FieldSerializer(),
        required=True,
        help_text="List of fields with names and optional types for the collection."
    )

    def validate_name(self, value):
        """Validate collection name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Collection name can only contain alphanumeric characters, underscores, or hyphens.")
        return value


class AddDatabasePOSTSerializer(serializers.Serializer):
    db_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the new database. Must be unique and only contain alphanumeric characters, underscores, or hyphens."
    )
    collections = serializers.ListField(
        child=CollectionSerializer(),
        required=False,
        help_text="List of collections with names and fields for the new database."
    )

    def validate(self, data):
        """Custom validation to make collections optional for 'living lab admin'."""
        collections = data.get("collections")

        if not collections:
            raise serializers.ValidationError("At least one collection with fields must be specified.")
        
        return data

    def validate_db_name(self, value):
        """Validate that db_name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
        if value.lower() == "admin":
            raise serializers.ValidationError("The database name 'admin' is reserved and cannot be used.")
        return value



class AddCollectionPOSTSerializer(serializers.Serializer):
    database_id = serializers.CharField(
        max_length=24,
        required=True,
        help_text="ID of the existing database where collections will be added"
    )
    collections = serializers.ListField(
        child=CollectionSerializer(),
        required=True,
        help_text="List of collections with names and document fields"
    )

    def validate_database_id(self, value):
        """Validate that database_id is a valid MongoDB ObjectId."""
        if not re.match(r'^[a-fA-F0-9]{24}$', value):
            raise serializers.ValidationError("Invalid database ID format. Must be a 24-character hexadecimal string.")
        return value


class GetMetadataSerializer(serializers.Serializer):
    db_name = serializers.CharField(required=True)

