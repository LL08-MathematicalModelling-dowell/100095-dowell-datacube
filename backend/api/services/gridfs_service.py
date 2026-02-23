"""
This module provides a service for handling file storage and retrieval using GridFS in MongoDB. 
It allows for uploading, downloading, and deleting files in a MongoDB database using GridFS, 
which is designed for storing large files that exceed the BSON-document size limit of 16MB. 
The service includes methods for saving files to GridFS, retrieving files by their ID, 
and deleting files from the database.
Each method is designed to interact with the MongoDB database using asynchronous operations,
ensuring efficient handling of file storage and retrieval tasks.
each user will have their own GridFS bucket, identified by a unique name that incorporates the user ID, 
ensuring that files are stored in a user-specific namespace within the database.
"""


from typing import AsyncIterable, Optional, Dict, Any
from django.conf import settings
from bson import ObjectId
from gridfs.asynchronous import AsyncGridFSBucket

from api.services.metadata_service import MetadataService

from typing import AsyncIterable, Optional, Dict, Any
from django.conf import settings
from bson import ObjectId
from gridfs.asynchronous import AsyncGridFSBucket

class GridFSService:
    def __init__(self, db_name: str, user_id: str, chunk_size: int = 1024 * 1024): # Default 1MB
        if not user_id:
            raise ValueError("GridFSService requires a valid user_id.")
            
        self.user_id = user_id
        self.client = settings.MONGODB_CLIENT 
        self.db = self.client[db_name]
        
        self.bucket_name = f"user_{self.user_id}_bucket"
        # Set chunk_size_bytes here to define how GridFS splits files
        self.bucket = AsyncGridFSBucket(
            self.db, 
            bucket_name=self.bucket_name,
            chunk_size_bytes=chunk_size
        )
        
        # self.meta_svc = MetadataService(user_id=user_id)

    async def upload_file_stream(
        self, 
        file_stream: AsyncIterable[bytes], 
        filename: str,
        content_type: str = None,
        custom_chunk_size: Optional[int] = None
    ) -> str:
        """
        Streams file data directly to GridFS.
        'custom_chunk_size' allows overriding the bucket default for specific uploads.
        """
        # 1. Prepare options
        upload_options = {
            "metadata": {"contentType": content_type, "owner": self.user_id}
        }
        if custom_chunk_size:
            upload_options["chunk_size_bytes"] = custom_chunk_size

        # 2. Use 'async with' for automatic closing and error handling
        async with self.bucket.open_upload_stream(filename, **upload_options) as grid_in:
            total_size = 0
            async for chunk in file_stream:
                # The driver handles buffering these chunks into GridFS blocks
                await grid_in.write(chunk)
                total_size += len(chunk)
            
            file_id_str = str(grid_in._id)

        # 3. Log to MetadataService
        await self.meta_svc.create_entry(
            file_id=file_id_str,
            filename=filename,
            size=total_size,
            content_type=content_type,
            storage_type="gridfs"
        )
        
        return file_id_str

    async def upload_file(self, file_data: bytes, filename: str, content_type: str = None) -> str:
        """
        Uploads a full byte buffer to GridFS.
        """
        # upload_from_stream takes (filename, source, **kwargs)
        grid_file_id = await self.bucket.upload_from_stream(
            filename, 
            file_data, 
            metadata={"contentType": content_type, "owner": self.user_id}
        )
        file_id_str = str(grid_file_id)

        await self.meta_svc.create_entry(
            file_id=file_id_str,
            filename=filename,
            size=len(file_data),
            content_type=content_type,
            storage_type="gridfs"
        )
        return file_id_str

    async def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Downloads a file from GridFS using its ID. Returns None if file not found.
        """
        try:
            # open_download_stream returns an AsyncGridOut object
            stream = await self.bucket.open_download_stream(ObjectId(file_id))
            return await stream.read()
        except Exception as e:
            # Log specific GridFS errors (e.g., NoFile)
            return None

    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves file metadata from the GridFS .files collection using AsyncCursor.
        """
        cursor = self.bucket.find({"_id": ObjectId(file_id)})
        results = await cursor.to_list(length=1) # Efficiently fetch one result
        
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
        """
        Deletes a file and cleans up the metadata entry.
        """
        try:
            # Delete from GridFS first
            await self.bucket.delete(ObjectId(file_id))
            # Only delete metadata if the storage deletion succeeds
            await self.meta_svc.delete_entry(file_id=file_id)
            return True
        except Exception:
            return False