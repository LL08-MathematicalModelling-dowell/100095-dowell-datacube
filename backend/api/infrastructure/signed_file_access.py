"""
Signed URL validation for GridFS file stream/download endpoints.

Resolves file owner from GridFS metadata and verifies HMAC signature query params.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from django.conf import settings
from django.http import Http404
from gridfs.asynchronous import AsyncGridFSBucket
from rest_framework import status
from rest_framework.response import Response

from api.infrastructure.signing import verify_signed_url


class SignedFileAccessError(Exception):
    """Invalid or missing signed URL parameters."""


def parse_signed_query_params(request) -> tuple[int, str]:
    """Extract and validate expires/sig from the request query string."""
    expires = request.GET.get("expires")
    signature = request.GET.get("sig")
    if not expires or not signature:
        raise SignedFileAccessError("Missing signature parameters.")
    try:
        return int(expires), str(signature)
    except ValueError as exc:
        raise SignedFileAccessError("Invalid expiration.") from exc


def unauthorized_response(detail: str, *, status_code: int = status.HTTP_401_UNAUTHORIZED) -> Response:
    return Response({"success": False, "detail": detail}, status=status_code)


async def resolve_gridfs_owner_id(file_id: str) -> Any:
    """
    Look up the owning user_id from GridFS metadata (no user JWT required).

    Raises Http404 when the file does not exist.
    """
    client = settings.MONGODB_CLIENT
    db = client[settings.FILE_STORAGE_DB_NAME]
    system_bucket = AsyncGridFSBucket(db, bucket_name="user_storage")

    try:
        cursor = system_bucket.find({"_id": ObjectId(file_id)}).limit(1)
        file_docs = await cursor.to_list(length=1)
        if not file_docs:
            raise Http404("File not found")
        owner_id = file_docs[0].metadata.get("user_id")
        if not owner_id:
            raise Http404("File not found")
        return owner_id
    except Http404:
        raise
    except Exception as exc:
        raise Http404(f"Error fetching file metadata: {exc}") from exc


async def authorize_signed_file_request(request, file_id: str) -> tuple[Any, int, str]:
    """
    Validate signed URL query params and return (owner_id, expires_int, signature).

    Raises SignedFileAccessError or Http404; returns Response only via helper above.
    """
    expires_int, signature = parse_signed_query_params(request)
    owner_id = await resolve_gridfs_owner_id(file_id)
    if not verify_signed_url(file_id, owner_id, expires_int, signature):
        raise SignedFileAccessError("Invalid/Expired signature")
    return owner_id, expires_int, signature
