"""Service for managing documents in a MongoDB collection."""

import json
from bson import ObjectId

def to_object_id(oid):
    try:
        return ObjectId(oid)
    except Exception:
        raise ValueError(f"Invalid ObjectId: {oid}")

def jsonify_object_ids(docs):
    """
    Convert any ObjectId in `_id` to string for JSON serialization.
    """
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
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




# import json
# from bson import ObjectId
# from rest_framework import status
# from rest_framework.response import Response


# def to_object_id(oid):
#     """ Convert a string to ObjectId."""
#     try:
#         return ObjectId(oid)
#     except Exception:
#         raise ValueError(f"Invalid ObjectId: {oid}")

# def jsonify_object_ids(docs):
#     """
#     Recursively convert ObjectId keys to str.
#     """
#     for doc in docs:
#         if "_id" in doc:
#             doc["_id"] = str(doc["_id"])
#     return docs

# def safe_load_filters(f):
#     """
#     Accept either a dict or a JSON string. Return a dict.
#     """
#     if isinstance(f, dict):
#         return f
#     try:
#         return json.loads(f or "{}")
#     except (TypeError, ValueError, json.JSONDecodeError):
#         return {}