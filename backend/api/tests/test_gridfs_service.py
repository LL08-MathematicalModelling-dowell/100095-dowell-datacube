import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock, call, ANY

pytestmark = pytest.mark.asyncio


class TestGridFSService:
    """Tests for GridFSService."""

    async def test_init(self, gridfs_service, user_id, mock_mongo_client):
        """Test service initialization sets up bucket and metadata service."""
        assert gridfs_service.user_id == user_id
        assert gridfs_service.bucket_name == f"user_{user_id}_bucket"
        mock_mongo_client.__getitem__.assert_called_with("test_files")
        # Metadata service is instantiated
        from api.services.metadata_service import MetadataService
        assert isinstance(gridfs_service.meta_svc, MetadataService)

    async def test_upload_file_stream(self, gridfs_service, mocker, file_id):
        """Test streaming file upload with progress callback."""
        # Mock the async context manager for open_upload_stream
        mock_grid_in = AsyncMock()
        mock_grid_in._id = ObjectId(file_id)
        mock_upload_stream = AsyncMock()
        mock_upload_stream.__aenter__.return_value = mock_grid_in
        gridfs_service.bucket.open_upload_stream = MagicMock(return_value=mock_upload_stream)

        # Mock metadata service
        mock_create_entry = mocker.patch.object(gridfs_service.meta_svc, "create_file_entry", new=AsyncMock())

        # Create a mock async file stream
        async def file_chunks():
            yield b"chunk1"
            yield b"chunk2"

        progress_callback = AsyncMock()

        result_id = await gridfs_service.upload_file_stream(
            file_stream=file_chunks(),
            filename="test.txt",
            content_type="text/plain",
            progress_callback=progress_callback
        )

        # Verify bucket.open_upload_stream called
        gridfs_service.bucket.open_upload_stream.assert_called_once_with(
            "test.txt",
            metadata={"contentType": "text/plain", "owner": gridfs_service.user_id}
        )

        # Verify write calls and progress
        mock_grid_in.write.assert_has_awaits([call(b"chunk1"), call(b"chunk2")])
        progress_callback.assert_has_awaits([call(5), call(10)])  # chunk lengths

        # Verify metadata creation
        mock_create_entry.assert_awaited_once_with(
            file_id=str(mock_grid_in._id),
            filename="test.txt",
            size=10,
            content_type="text/plain",
            storage_type="gridfs"
        )

        assert result_id == str(mock_grid_in._id)

    async def test_upload_file(self, gridfs_service, mocker, file_id):
        """Test uploading a full byte buffer."""
        # Mock upload_from_stream
        gridfs_service.bucket.upload_from_stream = AsyncMock(return_value=ObjectId(file_id))

        # Mock metadata service
        mock_create_entry = mocker.patch.object(gridfs_service.meta_svc, "create_file_entry", new=AsyncMock())

        file_data = b"hello world"
        result_id = await gridfs_service.upload_file(
            file_data=file_data,
            filename="test.txt",
            content_type="text/plain"
        )

        gridfs_service.bucket.upload_from_stream.assert_called_once_with(
            "test.txt",
            file_data,
            metadata={"contentType": "text/plain", "owner": gridfs_service.user_id}
        )
        mock_create_entry.assert_awaited_once_with(
            file_id=file_id,
            filename="test.txt",
            size=len(file_data),
            content_type="text/plain",
            storage_type="gridfs"
        )
        assert result_id == file_id

    async def test_download_file(self, gridfs_service, file_id):
        """Test downloading a file successfully."""
        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=b"file content")
        gridfs_service.bucket.open_download_stream = AsyncMock(return_value=mock_stream)

        result = await gridfs_service.download_file(file_id)

        gridfs_service.bucket.open_download_stream.assert_called_once_with(ObjectId(file_id))
        mock_stream.read.assert_awaited_once()
        assert result == b"file content"

    async def test_download_file_not_found(self, gridfs_service, file_id):
        """Test downloading a non-existent file returns None."""
        gridfs_service.bucket.open_download_stream = AsyncMock(side_effect=Exception("NoFile"))

        result = await gridfs_service.download_file(file_id)

        assert result is None

    async def test_get_file_info(self, gridfs_service, file_id):
        """Test retrieving file metadata from GridFS."""
        # Mock cursor returned by find()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            MagicMock(
                filename="test.txt",
                upload_date="2023-01-01",
                length=123,
                metadata={"contentType": "text/plain"}
            )
        ])
        gridfs_service.bucket.find = MagicMock(return_value=mock_cursor)

        result = await gridfs_service.get_file_info(file_id)

        gridfs_service.bucket.find.assert_called_once_with({"_id": ObjectId(file_id)})
        mock_cursor.to_list.assert_called_once_with(length=1)
        assert result == {
            "filename": "test.txt",
            "upload_date": "2023-01-01",
            "length": 123,
            "metadata": {"contentType": "text/plain"}
        }

    async def test_get_file_info_not_found(self, gridfs_service, file_id):
        """Test retrieving info for non-existent file returns None."""
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        gridfs_service.bucket.find = MagicMock(return_value=mock_cursor)

        result = await gridfs_service.get_file_info(file_id)

        assert result is None

    async def test_delete_file_success(self, gridfs_service, mocker, file_id):
        """Test deleting a file successfully."""
        gridfs_service.bucket.delete = AsyncMock()
        mock_delete_entry = mocker.patch.object(gridfs_service.meta_svc, "delete_file_entry", new=AsyncMock(return_value=True))

        result = await gridfs_service.delete_file(file_id)

        gridfs_service.bucket.delete.assert_awaited_once_with(ObjectId(file_id))
        mock_delete_entry.assert_awaited_once_with(file_id=file_id)
        assert result is True

    async def test_delete_file_failure(self, gridfs_service, mocker, file_id):
        """Test delete failure when bucket.delete raises exception."""
        gridfs_service.bucket.delete = AsyncMock(side_effect=Exception("Deletion error"))
        mock_delete_entry = mocker.patch.object(gridfs_service.meta_svc, "delete_file_entry", new=AsyncMock())

        result = await gridfs_service.delete_file(file_id)

        gridfs_service.bucket.delete.assert_awaited_once()
        mock_delete_entry.assert_not_awaited()
        assert result is False
