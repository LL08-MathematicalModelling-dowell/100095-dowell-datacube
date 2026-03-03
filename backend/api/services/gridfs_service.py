from typing import Optional, Dict, Any, Callable, Awaitable
from django.conf import settings
from gridfs.asynchronous import AsyncGridFSBucket
from bson import ObjectId
from api.services.metadata_service import MetadataService


ProgressCallback = Callable[[int], Awaitable[None]]


class GridFSService:
    """Service for handling file storage and retrieval using MongoDB's GridFS, scoped to individual users."""
    def __init__(self, db_name: str, user_id: str, chunk_size: int = 1024 * 1024):
        self.user_id = user_id
        self.client = settings.MONGODB_CLIENT 
        self.db = self.client[db_name]
        self.bucket = AsyncGridFSBucket(self.db, bucket_name="user_storage", chunk_size_bytes=chunk_size)
        self.meta_svc = MetadataService(user_id=user_id)

    async def upload_file_stream(
            self, file_stream,
            filename, content_type=None,
            progress_callback=None
        ) -> str:
        """Uploads a file to GridFS using an async stream."""
        async with self.bucket.open_upload_stream(
            filename,
            metadata={"contentType": content_type, "user_id": self.user_id}) as grid_in:
            total_uploaded = 0
            async for chunk in file_stream:
                await grid_in.write(chunk)
                total_uploaded += len(chunk)
                if progress_callback: await progress_callback(total_uploaded)
            file_id_str = str(grid_in._id)

        await self.meta_svc.create_file_entry(
            file_id=file_id_str,
            filename=filename,
            size=total_uploaded,
            content_type=content_type,
            storage_type="gridfs"
        )
        
        return file_id_str

    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves file metadata information for a given file_id, scoped to the user."""
        cursor = self.bucket.find({"_id": ObjectId(file_id), "metadata.user_id": self.user_id})
        results = await cursor.to_list(length=1)
        if results:
            file_doc = results[0]
            return {
                "filename": file_doc.filename,
                "upload_date": file_doc.upload_date,
                "length": file_doc.length,
                "metadata": file_doc.metadata
            }
        return None

    async def delete_file(self, file_id: str) -> bool:
        """Deletes a file from GridFS and its metadata entry, scoped to the user."""
        try:
            entry = await self.meta_svc.get_file_entry(file_id)
            if not entry: return False
            await self.bucket.delete(ObjectId(file_id))
            await self.meta_svc.delete_file_entry(file_id=file_id)
            return True
        except Exception: return False
