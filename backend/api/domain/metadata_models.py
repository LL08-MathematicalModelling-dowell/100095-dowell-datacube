"""
Canonical metadata document shape stored in MongoDB (METADATA_COLLECTION).

Each user owns logical databases; each database document tracks display name,
internal MongoDB database name, and collection schemas (field name + type).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict

from bson import ObjectId

# Types accepted on create/update via API serializers (subset of inferred types).
FIELD_TYPE_CHOICES: tuple[str, ...] = (
    "string",
    "integer",
    "number",
    "float",
    "double",
    "boolean",
    "date",
    "datetime",
    "object",
    "array",
    "null",
    "objectid",
    "binary",
    "decimal128",
    "timestamp",
)

# Aliases from clients or legacy data → canonical type string.
_FIELD_TYPE_ALIASES: dict[str, str] = {
    "str": "string",
    "text": "string",
    "int": "integer",
    "long": "integer",
    "num": "number",
    "bool": "boolean",
    "dict": "object",
    "list": "array",
    "oid": "objectid",
    "regex": "string",
}


class CollectionFieldMeta(TypedDict):
    name: str
    type: str


class CollectionMeta(TypedDict, total=False):
    name: str
    created_at: datetime
    fields: list[CollectionFieldMeta]


class PruningConfig(TypedDict, total=False):
    enabled: bool
    inactive_days: int
    last_pruned_at: datetime


class DatabaseMetadata(TypedDict, total=False):
    """User-scoped database metadata document."""

    _id: ObjectId
    user_id: ObjectId
    displayName: str
    dbName: str
    created_at: datetime
    updated_at: datetime
    collections: list[CollectionMeta]
    pruning: PruningConfig


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_display_name(name: str) -> str:
    """Canonical display name for uniqueness checks (case-insensitive)."""
    return name.strip().lower()


def normalize_field_type(value: str | None, *, default: str = "string") -> str:
    """Map client/inferred type strings to a canonical type label."""
    if not value:
        return default
    key = str(value).strip().lower()
    if key in _FIELD_TYPE_ALIASES:
        return _FIELD_TYPE_ALIASES[key]
    if key.startswith("array"):
        return key  # e.g. array<string>
    if key in FIELD_TYPE_CHOICES:
        return key
    return default


def format_collection_schema(
    collections: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> list[CollectionMeta]:
    """Build collection metadata blocks for persistence."""
    ts = now or utc_now()
    formatted: list[CollectionMeta] = []
    for coll in collections:
        fields_in: list[dict[str, Any]] = coll.get("fields") or []
        formatted.append(
            {
                "name": coll["name"],
                "created_at": coll.get("created_at") or ts,
                "fields": [
                    {
                        "name": f["name"],
                        "type": normalize_field_type(f.get("type")),
                    }
                    for f in fields_in
                ],
            }
        )
    return formatted


def new_database_metadata(
    *,
    user_id: ObjectId,
    display_name: str,
    internal_db_name: str,
    collections: list[dict[str, Any]],
) -> DatabaseMetadata:
    """Create a new database metadata document (before insert)."""
    now = utc_now()
    return {
        "user_id": user_id,
        "displayName": display_name.strip(),
        "dbName": internal_db_name,
        "created_at": now,
        "updated_at": now,
        "collections": format_collection_schema(collections, now=now),
    }


def infer_field_type(value: Any) -> str:
    """Infer a canonical field type from a BSON/Python value (schema learning)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, ObjectId):
        return "objectid"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return "array"
        inner = infer_field_type(value[0])
        return f"array<{inner}>"
    if isinstance(value, dict):
        return "object"
    return "string"


def serialize_metadata_doc(doc: Any) -> Any:
    """Recursively convert ObjectId/datetime for JSON responses."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_metadata_doc(item) for item in doc]
    if isinstance(doc, dict):
        out: dict[str, Any] = {}
        for key, val in doc.items():
            if isinstance(val, ObjectId):
                out[key] = str(val)
            elif isinstance(val, datetime):
                out[key] = val.isoformat()
            elif isinstance(val, (dict, list)):
                out[key] = serialize_metadata_doc(val)
            else:
                out[key] = val
        return out
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc
