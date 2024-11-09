import re
from rest_framework import serializers
from django.core.validators import MaxValueValidator


class InputGetSerializer(serializers.Serializer):
    operations = [
        ('insert', 'insert'),
        ('update', 'update'),
        ('delete', 'delete'),
        ('fetch', 'fetch'),
    ]
    # choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']

    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    operation = serializers.ChoiceField(choices=operations, required=True)
    filters = serializers.JSONField(required=False)
    # api_key = serializers.CharField(max_length=510, required=True)
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)
    # payment = serializers.BooleanField(default=True, allow_null=True, required=False)
    # data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class InputPostSerializer(serializers.Serializer):
    operations = [
        ('insert', 'insert'),
        ('update', 'update'),
        ('delete', 'delete'),
        ('fetch', 'fetch'),
    ]
    # choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']
    
    # api_key = serializers.CharField(max_length=510, required=True)
    coll_name = serializers.CharField(max_length=255, required=True)
    db_name = serializers.CharField(max_length=255, required=True)
    operation = serializers.ChoiceField(choices=operations, required=True)
    data = serializers.JSONField(required=True)
    # payment = serializers.BooleanField(default=True, allow_null=True, required=False)
    # is_deleted = serializers.BooleanField(default=False)
    # data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class InputPutSerializer(serializers.Serializer):
    # choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']
    # api_key = serializers.CharField(max_length=510, required=True)
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=10)
    query = serializers.JSONField(required=False)
    update_data = serializers.JSONField(required=False)
    # payment = serializers.BooleanField(default=True, allow_null=True, required=False)
    # data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


class InputDeleteSerializer(serializers.Serializer):
    # choose_data_type = ['real_data', 'testing_data', 'learning_data', 'deleted_data']
    # api_key = serializers.CharField(max_length=510)
    db_name = serializers.CharField(max_length=100)
    coll_name = serializers.CharField(max_length=100)
    operation = serializers.CharField(max_length=10)
    query = serializers.JSONField(required=False)
    # data_type = serializers.ChoiceField(choices=choose_data_type, required=True)


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


# =================== Create Database ===================

# class CollectionFieldSerializer(serializers.Serializer):
#     name = serializers.CharField(
#         max_length=100,
#         required=True,
#         help_text="Name of the collection to be created"
#     )
#     fields = serializers.ListField(
#         child=serializers.CharField(max_length=100),
#         required=True,
#         help_text="List of field names for documents in the collection"
#     )

#     def validate_name(self, value):
#         """Validate collection name contains only allowed characters."""
#         if not re.match(r'^[\w-]+$', value):
#             raise serializers.ValidationError("Collection name can only contain alphanumeric characters, underscores, or hyphens.")
#         return value

#     def validate_fields(self, value):
#         """Validate each field name in the list."""
#         invalid_fields = [field for field in value if not re.match(r'^[\w-]+$', field)]
#         if invalid_fields:
#             raise serializers.ValidationError(f"Invalid field names: {', '.join(invalid_fields)}. Only alphanumeric characters, underscores, and hyphens are allowed.")
#         return value


# class AddDatabasePOSTSerializer(serializers.Serializer):
#     db_name = serializers.CharField(
#         max_length=100,
#         required=True,
#         help_text="Name of the new database"
#     )
#     product_name = serializers.CharField(
#         max_length=100,
#         required=False,
#         allow_blank=True,
#         help_text="Optional product name to configure specific database setup"
#     )
#     collections = serializers.ListField(
#         child=CollectionFieldSerializer(),
#         required=True,
#         help_text="List of collections with names and document fields"
#     )

#     def validate_db_name(self, value):
#         """Validate that db_name contains only allowed characters."""
#         if not re.match(r'^[\w-]+$', value):
#             raise serializers.ValidationError("Database name can only contain alphanumeric characters, underscores, or hyphens.")
#         return value


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


