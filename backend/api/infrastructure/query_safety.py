"""Validation helpers for MongoDB filters and update documents on CRUD endpoints."""

from __future__ import annotations

from typing import Any, Dict, Tuple

# Operators that must never appear in user-supplied filters.
FORBIDDEN_FILTER_KEYS = frozenset({"$where", "$function", "$accumulator", "$expr"})

# Update operators allowed on PUT (no cross-collection or aggregation stages).
ALLOWED_UPDATE_OPERATORS = frozenset(
    {
        "$set",
        "$inc",
        "$unset",
        "$push",
        "$pull",
        "$addToSet",
        "$rename",
        "$min",
        "$max",
        "$mul",
        "$currentDate",
    }
)

FORBIDDEN_UPDATE_KEYS = frozenset({"$out", "$merge", "$replaceRoot", "$replaceWith"})

MAX_INSERT_BATCH = 500


def _walk_filter(node: Any, *, path: str = "") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in FORBIDDEN_FILTER_KEYS:
                raise ValueError(f"Filter operator '{key}' is not allowed.")
            if key.startswith("$") and key not in (
                "$and",
                "$or",
                "$nor",
                "$in",
                "$nin",
                "$eq",
                "$ne",
                "$gt",
                "$gte",
                "$lt",
                "$lte",
                "$exists",
                "$regex",
                "$not",
                "$elemMatch",
                "$size",
                "$type",
                "$all",
            ):
                # Allow common comparison/logical operators only.
                if key not in FORBIDDEN_FILTER_KEYS:
                    pass  # other $ operators on field paths are field-level, validated at key level
            _walk_filter(value, path=f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for item in node:
            _walk_filter(item, path=path)


def validate_filter(filt: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(filt, dict):
        raise ValueError("filters must be a JSON object.")
    _walk_filter(filt)
    return filt


def assert_filter_not_empty(filt: Dict[str, Any]) -> None:
    if not filt:
        raise ValueError("filters must not be empty.")


def filter_targets_single_id(filt: Dict[str, Any]) -> bool:
    return "_id" in filt or "id" in filt


def assert_single_document_filter(filt: Dict[str, Any]) -> None:
    assert_filter_not_empty(filt)
    if not filter_targets_single_id(filt):
        raise ValueError(
            "Single-document updates require '_id' or 'id' in filters, "
            "or set update_many to true for multi-document updates."
        )


def assert_mutating_filter_allowed(filt: Dict[str, Any], *, update_many: bool = False) -> None:
    assert_filter_not_empty(filt)
    if not update_many and not filter_targets_single_id(filt):
        raise ValueError(
            "Non-empty filters must include '_id' or 'id' unless update_many is true."
        )


def is_operator_update(update_data: Dict[str, Any]) -> bool:
    return any(str(k).startswith("$") for k in update_data)


def prepare_update_document(update_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Normalize client update_data into a MongoDB update document.

    Returns (update_doc, sample_for_schema) where sample_for_schema is a flat
  dict of fields to feed schema inference.
    """
    if not update_data:
        raise ValueError("update_data must not be empty.")

    if is_operator_update(update_data):
        for key in update_data:
            if key in FORBIDDEN_UPDATE_KEYS:
                raise ValueError(f"Update operator '{key}' is not allowed.")
            if key.startswith("$") and key not in ALLOWED_UPDATE_OPERATORS:
                raise ValueError(f"Update operator '{key}' is not allowed.")
        schema_sample = update_data.get("$set")
        if isinstance(schema_sample, dict):
            return update_data, schema_sample
        return update_data, {}

    return {"$set": update_data}, update_data


def plain_fields_for_partial_update(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a flat field map for pipeline updates (existing-fields-only mode)."""
    if not is_operator_update(update_data):
        return dict(update_data)
    if set(update_data.keys()) == {"$set"} and isinstance(update_data["$set"], dict):
        return dict(update_data["$set"])
    raise ValueError(
        "Partial updates (update_all_fields=false) require a plain field map "
        "or a single $set object."
    )
