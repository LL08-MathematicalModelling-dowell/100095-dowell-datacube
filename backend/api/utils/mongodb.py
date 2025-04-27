"""Service for managing documents in a MongoDB collection."""

import json
from bson import ObjectId
from rest_framework import status
from rest_framework.response import Response


def to_object_id(oid):
    """ Convert a string to ObjectId."""
    try:
        return ObjectId(oid)
    except Exception:
        raise ValueError(f"Invalid ObjectId: {oid}")

def jsonify_object_ids(docs):
    """
    Recursively convert ObjectId keys to str.
    """
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs

def safe_load_filters(f_str):
    """ Safely load filters from a string."""
    try:
        return json.loads(f_str or "{}")
    except json.JSONDecodeError:
        return {}