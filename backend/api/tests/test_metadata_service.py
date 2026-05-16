import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio


class TestMetadataServiceFileMethods:
    """Tests for MetadataService file metadata helpers."""

    async def test_create_file_entry(self, metadata_service, mock_file_metadata_collection, file_id):
        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId()
        mock_file_metadata_collection.insert_one = AsyncMock(return_value=insert_result)

        result = await metadata_service.create_file_entry(
            file_id=file_id,
            filename="test.txt",
            size=1024,
            content_type="text/plain",
            storage_type="gridfs",
        )

        mock_file_metadata_collection.insert_one.assert_awaited_once()
        call_args = mock_file_metadata_collection.insert_one.await_args[0][0]
        assert call_args["user_id"] == metadata_service.user_id
        assert call_args["file_id"] == file_id
        assert call_args["filename"] == "test.txt"
        assert call_args["size"] == 1024
        assert call_args["content_type"] == "text/plain"
        assert call_args["storage_type"] == "gridfs"
        assert "uploaded_at" in call_args
        assert "updated_at" in call_args

        assert result["_id"] == str(insert_result.inserted_id)

    async def test_delete_file_entry(self, metadata_service, mock_file_metadata_collection, file_id):
        delete_result = MagicMock()
        delete_result.deleted_count = 1
        mock_file_metadata_collection.delete_one = AsyncMock(return_value=delete_result)

        result = await metadata_service.delete_file_entry(file_id)

        assert result is True
        mock_file_metadata_collection.delete_one.assert_awaited_once_with(
            {"user_id": metadata_service.user_id, "file_id": file_id},
            session=None,
        )

    async def test_delete_file_entry_not_found(self, metadata_service, mock_file_metadata_collection, file_id):
        delete_result = MagicMock()
        delete_result.deleted_count = 0
        mock_file_metadata_collection.delete_one = AsyncMock(return_value=delete_result)

        result = await metadata_service.delete_file_entry(file_id)

        assert result is False

    async def test_get_file_entry(self, metadata_service, mock_file_metadata_collection, file_id):
        oid = ObjectId()
        raw_doc = {"_id": oid, "file_id": file_id, "filename": "test.txt"}
        mock_file_metadata_collection.find_one = AsyncMock(return_value=raw_doc)

        result = await metadata_service.get_file_entry(file_id)

        assert result == {"_id": str(oid), "file_id": file_id, "filename": "test.txt"}
        mock_file_metadata_collection.find_one.assert_awaited_once_with(
            {"user_id": metadata_service.user_id, "file_id": file_id}
        )

    async def test_list_files_paginated(self, metadata_service, mock_file_metadata_collection):
        mock_file_metadata_collection.count_documents = AsyncMock(return_value=10)

        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        o1, o2 = ObjectId(), ObjectId()
        mock_cursor.to_list = AsyncMock(
            return_value=[
                {"_id": o1, "file_id": "f1", "filename": "a.txt"},
                {"_id": o2, "file_id": "f2", "filename": "b.txt"},
            ]
        )
        mock_file_metadata_collection.find = MagicMock(return_value=mock_cursor)

        total, docs = await metadata_service.list_files_paginated(
            page=2, page_size=5, search_term="test"
        )

        assert total == 10
        assert len(docs) == 2
        assert docs[0]["_id"] == str(o1)
        assert docs[1]["_id"] == str(o2)

        mock_file_metadata_collection.count_documents.assert_awaited_once_with(
            {"user_id": metadata_service.user_id, "filename": {"$regex": "test", "$options": "i"}}
        )
        mock_file_metadata_collection.find.assert_called_once_with(
            {"user_id": metadata_service.user_id, "filename": {"$regex": "test", "$options": "i"}}
        )
        mock_cursor.sort.assert_called_once_with("uploaded_at", -1)
        mock_cursor.skip.assert_called_once_with(5)
        mock_cursor.limit.assert_called_once_with(5)
