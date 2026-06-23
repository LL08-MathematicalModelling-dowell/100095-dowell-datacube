import pytest
from bson import ObjectId
from unittest.mock import AsyncMock

from api.application.document_service import DocumentService
from api.presentation.serializers import BulkUpdateDocumentSerializer


def test_bulk_serializer_rejects_upsert_without_update_all_fields():
    serializer = BulkUpdateDocumentSerializer(
        data={
            "database_id": str(ObjectId()),
            "collection_name": "users",
            "operations": [
                {
                    "filters": {"_id": str(ObjectId())},
                    "update_data": {"points": 1},
                    "upsert": True,
                }
            ],
        }
    )
    assert serializer.is_valid() is False
    assert "upsert" in serializer.errors["operations"][0]


def test_bulk_serializer_requires_id_per_operation():
    serializer = BulkUpdateDocumentSerializer(
        data={
            "database_id": str(ObjectId()),
            "collection_name": "users",
            "operations": [
                {
                    "filters": {"status": "active"},
                    "update_data": {"points": 1},
                    "update_all_fields": True,
                }
            ],
        }
    )
    assert serializer.is_valid() is False
    assert "filters" in serializer.errors["operations"][0]


@pytest.mark.django_db
def test_crud_bulk_endpoint(authenticated_api_client, mocker):
    database_id = str(ObjectId())
    mock_response = {
        "matched_count": 1,
        "modified_count": 1,
        "upserted_count": 1,
        "results": [
            {"index": 0, "ok": True},
            {"index": 1, "ok": True, "upserted_id": str(ObjectId())},
        ],
    }
    mocker.patch(
        "api.application.document_service.DocumentService.bulk_update_docs",
        new=AsyncMock(return_value=mock_response),
    )

    url = "/api/v2/crud/bulk/"
    data = {
        "database_id": database_id,
        "collection_name": "users",
        "operations": [
            {
                "filters": {"_id": str(ObjectId())},
                "update_data": {"points": 120},
                "update_all_fields": True,
                "upsert": True,
            },
            {
                "filters": {"_id": str(ObjectId())},
                "update_data": {"points": 450},
                "update_all_fields": True,
                "upsert": True,
            },
        ],
    }
    response = authenticated_api_client.post(url, data=data, format="json")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["upserted_count"] == 1
    assert len(body["results"]) == 2


def test_format_bulk_write_response_marks_failed_indices():
    body = DocumentService._format_bulk_write_response(
        op_count=2,
        matched_count=1,
        modified_count=1,
        upserted_count=0,
        upserted_by_index={},
        write_errors=[{"index": 1, "errmsg": "duplicate key"}],
    )
    assert body["results"][0]["ok"] is True
    assert body["results"][1]["ok"] is False
    assert body["results"][1]["error"] == "duplicate key"
    assert len(body["errors"]) == 1
