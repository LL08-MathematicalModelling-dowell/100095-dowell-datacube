from typing import List, Dict, Any
import re
from bson import ObjectId

class ValidationError(Exception):
    """
    Custom exception for validation errors.

    Attributes:
        message (str): Error message.
        field (str): Field name related to the error.
        code (str): Optional error code.
    """
    def __init__(self, message: str, field: str = "", code: str = ""):
        super().__init__(message)
        self.message = message
        self.field = field
        self.code = code

    def __str__(self):
        return f"{self.message} (field: {self.field}, code: {self.code})"

def validate_database_name(name: str) -> None:
    """
    Validates the name of the database.

    Args:
        name (str): The database name.

    Raises:
        ValidationError: If the database name is invalid.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValidationError(
            "Database name must be a non-empty string.",
            field="database_name",
            code="DB_NAME_INVALID"
        )

    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        raise ValidationError(
            "Database name can only contain alphanumeric characters and underscores.",
            field="database_name",
            code="DB_NAME_FORMAT_ERROR"
        )

def validate_collections(collections: List[Dict[str, Any]]) -> None:
    """
    Validates the structure of collections.

    Args:
        collections (List[Dict[str, Any]]): A list of collection definitions.

    Raises:
        ValidationError: If the collection definitions are invalid.
    """
    if not isinstance(collections, list):
        raise ValidationError(
            "Collections must be a list of dictionaries.",
            field="collections",
            code="COLLECTIONS_NOT_LIST"
        )

    for collection in collections:
        if not isinstance(collection, dict):
            raise ValidationError(
                "Each collection must be a dictionary.",
                field="collections",
                code="COLLECTION_NOT_DICT"
            )

        if "name" not in collection or not isinstance(collection["name"], str) or not collection["name"].strip():
            raise ValidationError(
                "Each collection must have a valid 'name'.",
                field="collection_name",
                code="COLLECTION_NAME_INVALID"
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", collection["name"]):
            raise ValidationError(
                f"Collection name '{collection['name']}' is invalid. Only alphanumeric characters and underscores are allowed.",
                field="collection_name",
                code="COLLECTION_NAME_FORMAT_ERROR"
            )

        if "fields" not in collection or not isinstance(collection["fields"], list):
            raise ValidationError(
                f"Collection '{collection['name']}' must have a 'fields' key with a list of field definitions.",
                field="fields",
                code="FIELDS_MISSING_OR_INVALID"
            )

        for field in collection["fields"]:
            if not isinstance(field, dict):
                raise ValidationError(
                    f"Fields in collection '{collection['name']}' must be dictionaries.",
                    field="field_definition",
                    code="FIELD_NOT_DICT"
                )

            if "name" not in field or not isinstance(field["name"], str) or not field["name"].strip():
                raise ValidationError(
                    f"Each field in collection '{collection['name']}' must have a valid 'name'.",
                    field="field_name",
                    code="FIELD_NAME_INVALID"
                )

            if not re.match(r"^[a-zA-Z0-9_]+$", field["name"]):
                raise ValidationError(
                    f"Field name '{field['name']}' in collection '{collection['name']}' is invalid.",
                    field="field_name",
                    code="FIELD_NAME_FORMAT_ERROR"
                )

            if "type" not in field or field["type"] not in {"string", "integer", "boolean", "float", "date"}:
                raise ValidationError(
                    f"Field '{field['name']}' in collection '{collection['name']}' has an invalid or missing type.",
                    field="field_type",
                    code="FIELD_TYPE_INVALID"
                )

def validate_object_id(object_id: str) -> None:
    """
    Validates if a string is a valid MongoDB ObjectId.

    Args:
        object_id (str): The ObjectId to validate.

    Raises:
        ValidationError: If the ObjectId is invalid.
    """
    if not isinstance(object_id, str) or not object_id.strip():
        raise ValidationError(
            "ObjectId must be a non-empty string.",
            field="object_id",
            code="OBJECT_ID_INVALID"
        )

    try:
        ObjectId(object_id)
    except Exception:
        raise ValidationError(
            "Invalid ObjectId format.",
            field="object_id",
            code="OBJECT_ID_FORMAT_ERROR"
        )
