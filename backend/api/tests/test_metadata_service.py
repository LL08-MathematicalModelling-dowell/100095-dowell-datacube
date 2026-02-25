import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock, call

pytestmark = pytest.mark.asyncio


class TestMetadataServiceFileMethods:
    """Tests for the file metadata methods added to MetadataService."""

    async def test_create_file_entry(self, metadata_service, mock_file_metadata_collection, file_id):
        """Test creating a file metadata entry."""
        mock_insert = AsyncMock()
        mock_insert.inserted_id = ObjectId()
        mock_file_metadata_collection.insert_one = mock_insert

        result = await metadata_service.create_file_entry(
            file_id=file_id,
            filename="test.txt",
            size=1024,
            content_type="text/plain",
            storage_type="gridfs"
        )

        # Verify insert_one called with correct data
        mock_insert.assert_called_once()
        call_args = mock_insert.call_args[0][0]
        assert call_args["user_id"] == metadata_service.user_id
        assert call_args["file_id"] == file_id
        assert call_args["filename"] == "test.txt"
        assert call_args["size"] == 1024
        assert call_args["content_type"] == "text/plain"
        assert call_args["storage_type"] == "gridfs"
        assert "uploaded_at" in call_args
        assert "updated_at" in call_args

        # Verify returned dict includes _id
        assert result["_id"] == mock_insert.inserted_id

    async def test_delete_file_entry(self, metadata_service, mock_file_metadata_collection, file_id):
        """Test deleting a file metadata entry."""
        mock_delete = AsyncMock()
        mock_delete.deleted_count = 1
        mock_file_metadata_collection.delete_one = mock_delete

        result = await metadata_service.delete_file_entry(file_id)

        assert result is True
        mock_delete.assert_called_once_with(
            {"user_id": metadata_service.user_id, "file_id": file_id},
            session=None
        )

    async def test_delete_file_entry_not_found(self, metadata_service, mock_file_metadata_collection, file_id):
        """Test deleting a non-existent file returns False."""
        mock_delete = AsyncMock()
        mock_delete.deleted_count = 0
        mock_file_metadata_collection.delete_one = mock_delete

        result = await metadata_service.delete_file_entry(file_id)

        assert result is False

    async def test_get_file_entry(self, metadata_service, mock_file_metadata_collection, file_id):
        """Test retrieving a file metadata entry."""
        expected_doc = {"_id": ObjectId(), "file_id": file_id, "filename": "test.txt"}
        mock_find_one = AsyncMock(return_value=expected_doc)
        mock_file_metadata_collection.find_one = mock_find_one

        result = await metadata_service.get_file_entry(file_id)

        assert result == expected_doc
        mock_find_one.assert_called_once_with(
            {"user_id": metadata_service.user_id, "file_id": file_id}
        )

    async def test_list_files_paginated(self, metadata_service, mock_file_metadata_collection):
        """Test paginated listing of file metadata with search."""
        # Mock count_documents
        mock_count = AsyncMock(return_value=10)
        mock_file_metadata_collection.count_documents = mock_count

        # Mock cursor chain
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[
            {"_id": ObjectId(), "file_id": "f1", "filename": "a.txt"},
            {"_id": ObjectId(), "file_id": "f2", "filename": "b.txt"},
        ])
        mock_file_metadata_collection.find = MagicMock(return_value=mock_cursor)

        total, docs = await metadata_service.list_files_paginated(
            page=2, page_size=5, search_term="test"
        )

        assert total == 10
        assert len(docs) == 2
        # Verify _id converted to string
        for doc in docs:
            assert isinstance(doc["_id"], str)

        # Verify query construction
        mock_count.assert_called_once_with(
            {"user_id": metadata_service.user_id, "filename": {"$regex": "test", "$options": "i"}}
        )
        mock_file_metadata_collection.find.assert_called_once_with(
            {"user_id": metadata_service.user_id, "filename": {"$regex": "test", "$options": "i"}}
        )
        mock_cursor.sort.assert_called_once_with("uploaded_at", -1)
        mock_cursor.skip.assert_called_once_with(5)  # (page-1)*page_size = 5
        mock_cursor.limit.assert_called_once_with(5)

    async def test_create_entry_adapter(self, metadata_service, mocker, file_id):
        """Test the adapter method create_entry calls create_file_entry."""
        mock_create_file_entry = mocker.patch.object(
            metadata_service, "create_file_entry", new=AsyncMock()
        )
        mock_create_file_entry.return_value = {"_id": ObjectId()}

        result = await metadata_service.create_entry(
            file_id=file_id,
            filename="test.txt",
            size=1024,
            content_type="text/plain",
            storage_type="gridfs",
            session="mock_session"
        )

        mock_create_file_entry.assert_awaited_once_with(
            file_id, "test.txt", 1024, "text/plain", "gridfs", session="mock_session"
        )
        assert result == mock_create_file_entry.return_value

    async def test_delete_entry_adapter(self, metadata_service, mocker, file_id):
        """Test the adapter method delete_entry calls delete_file_entry."""
        mock_delete_file_entry = mocker.patch.object(
            metadata_service, "delete_file_entry", new=AsyncMock()
        )
        mock_delete_file_entry.return_value = True

        result = await metadata_service.delete_entry(file_id, session="mock_session")

        mock_delete_file_entry.assert_awaited_once_with(file_id, session="mock_session")
        assert result is True
