import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock, call

pytestmark = pytest.mark.asyncio


class TestGridFSService:
    """Tests for GridFSService (mocked AsyncGridFSBucket)."""

    async def test_init(self, gridfs_service, user_id, mock_mongo_client):
        assert gridfs_service.user_id == user_id
        mock_mongo_client.__getitem__.assert_called_with("test_files")
        from api.application.metadata_service import MetadataService

        assert isinstance(gridfs_service.meta_svc, MetadataService)

    async def test_upload_file_stream(self, gridfs_service, mocker, file_id):
        mock_grid_in = AsyncMock()
        mock_grid_in._id = ObjectId(file_id)
        mock_upload_ctx = AsyncMock()
        mock_upload_ctx.__aenter__.return_value = mock_grid_in
        mock_upload_ctx.__aexit__.return_value = None
        gridfs_service.bucket.open_upload_stream = MagicMock(return_value=mock_upload_ctx)

        mock_create_entry = mocker.patch.object(
            gridfs_service.meta_svc, "create_file_entry", new=AsyncMock()
        )

        async def file_chunks():
            yield b"chunk1"
            yield b"chunk2"

        progress_callback = AsyncMock()

        result_id = await gridfs_service.upload_file_stream(
            file_stream=file_chunks(),
            filename="test.txt",
            content_type="text/plain",
            progress_callback=progress_callback,
        )

        gridfs_service.bucket.open_upload_stream.assert_called_once_with(
            "test.txt",
            metadata={"contentType": "text/plain", "user_id": gridfs_service.user_id},
        )

        mock_grid_in.write.assert_has_awaits([call(b"chunk1"), call(b"chunk2")])
        progress_callback.assert_has_awaits([call(6), call(12)])

        mock_create_entry.assert_awaited_once_with(
            file_id=str(mock_grid_in._id),
            filename="test.txt",
            size=12,
            content_type="text/plain",
            storage_type="gridfs",
        )

        assert result_id == str(mock_grid_in._id)

    async def test_get_file_info(self, gridfs_service, file_id):
        grid_item = MagicMock()
        grid_item.filename = "test.txt"
        grid_item._id = ObjectId(file_id)
        grid_item.upload_date = "2023-01-01"
        grid_item.length = 123
        grid_item.metadata = {"contentType": "text/plain", "user_id": gridfs_service.user_id}

        mock_cursor = MagicMock()
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[grid_item])
        gridfs_service.bucket.find = MagicMock(return_value=mock_cursor)

        result = await gridfs_service.get_file_info(file_id)

        gridfs_service.bucket.find.assert_called_once_with(
            {"_id": ObjectId(file_id), "metadata.user_id": gridfs_service.user_id}
        )
        mock_cursor.limit.assert_called_once_with(1)
        mock_cursor.to_list.assert_awaited_once()

        assert result == {
            "filename": "test.txt",
            "file_id": str(ObjectId(file_id)),
            "content_type": "text/plain",
            "upload_date": "2023-01-01",
            "length": 123,
            "metadata": grid_item.metadata,
        }

    async def test_get_file_info_not_found(self, gridfs_service, file_id):
        mock_cursor = MagicMock()
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        gridfs_service.bucket.find = MagicMock(return_value=mock_cursor)

        result = await gridfs_service.get_file_info(file_id)

        assert result is None

    async def test_delete_file_success(self, gridfs_service, mocker, file_id):
        mocker.patch.object(
            gridfs_service.meta_svc,
            "get_file_entry",
            new=AsyncMock(return_value={"file_id": file_id, "_id": file_id}),
        )
        gridfs_service.bucket.delete = AsyncMock()
        mock_delete_entry = mocker.patch.object(
            gridfs_service.meta_svc, "delete_file_entry", new=AsyncMock()
        )

        result = await gridfs_service.delete_file(file_id)

        gridfs_service.bucket.delete.assert_awaited_once_with(ObjectId(file_id))
        mock_delete_entry.assert_awaited_once_with(file_id=file_id)
        assert result is True

    async def test_delete_file_no_metadata_returns_false(self, gridfs_service, mocker, file_id):
        mocker.patch.object(gridfs_service.meta_svc, "get_file_entry", new=AsyncMock(return_value=None))
        gridfs_service.bucket.delete = AsyncMock()

        result = await gridfs_service.delete_file(file_id)

        gridfs_service.bucket.delete.assert_not_called()
        assert result is False

    async def test_delete_file_bucket_error_returns_false(self, gridfs_service, mocker, file_id):
        mocker.patch.object(
            gridfs_service.meta_svc,
            "get_file_entry",
            new=AsyncMock(return_value={"file_id": file_id}),
        )
        gridfs_service.bucket.delete = AsyncMock(side_effect=RuntimeError("Deletion error"))
        mock_delete_entry = mocker.patch.object(
            gridfs_service.meta_svc, "delete_file_entry", new=AsyncMock()
        )

        result = await gridfs_service.delete_file(file_id)

        mock_delete_entry.assert_not_called()
        assert result is False
