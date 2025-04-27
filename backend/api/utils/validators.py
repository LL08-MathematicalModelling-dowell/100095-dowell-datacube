import re
from rest_framework.serializers import ValidationError

def sanitize_name(name: str) -> str:
    """Sanitize a name by replacing non-alphanumeric characters with underscores."""
    return re.sub(r"\W+", "_", name).lower()

def validate_collection_name(name: str):
    """Validate the collection name."""
    if len(name) > 100:
        raise ValidationError("Collection name too long (max 100).")

def validate_unique_fields(fields: list):
    """Validate that field names are unique."""
    names = [f["name"] for f in fields]
    if len(names) != len(set(names)):
        raise ValidationError("Field names must be unique.")