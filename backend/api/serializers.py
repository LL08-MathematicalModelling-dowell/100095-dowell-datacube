import re
from rest_framework import serializers
from django.core.validators import MaxValueValidator


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

class CollectionFieldSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the collection to be created"
    )
    fields = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        help_text="List of field names for documents in the collection"
    )

    def validate_name(self, value):
        """Validate collection name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Collection name can only contain alphanumeric characters, underscores, or hyphens.")
        return value

    def validate_fields(self, value):
        """Validate each field name in the list."""
        invalid_fields = [field for field in value if not re.match(r'^[\w-]+$', field)]
        if invalid_fields:
            raise serializers.ValidationError(f"Invalid field names: {', '.join(invalid_fields)}. Only alphanumeric characters, underscores, and hyphens are allowed.")
        return value


class AddCollectionPOSTSerializer(serializers.Serializer):
    db_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the existing database where collections will be added"
    )
    collections = serializers.ListField(
        child=CollectionFieldSerializer(),
        required=True,
        help_text="List of collections with names and document fields"
    )

    def validate_db_name(self, value):
        """Validate that db_name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
        return value


class CollectionFieldSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the collection to be created"
    )
    fields = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=True,
        help_text="List of field names for documents in the collection"
    )

    def validate_name(self, value):
        """Validate collection name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Collection name can only contain alphanumeric characters, underscores, or hyphens.")
        return value

    def validate_fields(self, value):
        """Validate each field name in the list."""
        invalid_fields = [field for field in value if not re.match(r'^[\w-]+$', field)]
        if invalid_fields:
            raise serializers.ValidationError(f"Invalid field names: {', '.join(invalid_fields)}. Only alphanumeric characters, underscores, and hyphens are allowed.")
        return value


class AddDatabasePOSTSerializer(serializers.Serializer):
    db_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Name of the new database"
    )
    product_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Optional product name to configure specific database setup"
    )
    collections = serializers.ListField(
        child=CollectionFieldSerializer(),
        required=False,
        help_text="List of collections with names and document fields"
    )

    def validate(self, data):
        """Custom validation to make collections optional for 'living lab admin'."""
        product_name = data.get("product_name", "").lower()
        collections = data.get("collections")

        # Ensure collections are specified for non-living lab products
        if product_name != "living lab admin" and not collections:
            raise serializers.ValidationError("At least one collection with fields must be specified if not using 'living lab admin'.")
        
        return data

    def validate_db_name(self, value):
        """Validate that db_name contains only allowed characters."""
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
        return value
