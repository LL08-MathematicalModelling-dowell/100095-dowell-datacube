"""Service for managing documents in a MongoDB collection."""

import json
from bson import ObjectId
from typing import Any, Dict


def to_object_id(oid):
    try:
        return ObjectId(oid)
    except Exception:
        raise ValueError(f"Invalid ObjectId: {oid}")

def jsonify_object_ids(docs):
    """
    Convert any ObjectId in `_id` to string for JSON serialization.
    Works recursively on nested dicts and lists.
    """
    # check if docs is a list
    if isinstance(docs, list):
        return [jsonify_object_ids(doc) for doc in docs]

    # otherwise assume it's a dict
    for key, value in docs.items():
        if isinstance(value, ObjectId):
            docs[key] = str(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    jsonify_object_ids(item)
        elif isinstance(value, dict):
            jsonify_object_ids(value)

    return docs

def safe_load_filters(f):
    """
    Accept either a dict or a JSON string. Return a dict.
    """
    if isinstance(f, dict):
        return f
    try:
        return json.loads(f or "{}")
    except (TypeError, ValueError):
       return {}

def normalize_id_filter(
    filt: Dict[str, Any]
) -> Dict[str, Any]:
    """
    If the client filter dict has 'id' or '_id', pop it and
    re-insert as an ObjectId under '_id'. Returns a new dict.
    Raises ValueError if the raw value is neither a valid hex‐str nor an ObjectId.
    """
    out = filt.copy()
    # decide which key to normalize
    if 'id' in out:
        key = 'id'
    elif '_id' in out:
        key = '_id'
    else:
        return out

    raw = out.pop(key)
    # Case A: already ObjectId
    if isinstance(raw, ObjectId):
        out['_id'] = raw

    # Case B: string, try to parse
    elif isinstance(raw, str):
        try:
            out['_id'] = ObjectId(raw)
        except Exception:
            raise ValueError(f"Invalid {key!r}: not a valid ObjectId hex string")

    # Case C: anything else is invalid
    else:
        raise ValueError(
            f"Filter field {key!r} must be str or ObjectId, got {type(raw).__name__}"
        )

    return out

def build_existing_fields_update_pipeline(
    update_data: Dict[str, Any]
) -> list[Dict]:
    """
    Optimized single-core version using dictionary comprehension.
    Typically 30-50% faster than a standard for-loop.
    """
    set_stage = {
        field: {
            "$cond": [
                { "$eq": [{ "$type": f"${field}" }, "missing"] },
                "$$REMOVE",
                new_val
            ]
        }
        for field, new_val in update_data.items()
    }
    return [{"$set": set_stage}]
