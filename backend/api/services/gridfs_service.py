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


class GridFSService:
    def __init__(self, db_name: str, user_id: str):
        if not user_id:
            raise ValueError("GridFSService requires a valid user_id.")
            
        self.user_id = user_id
        self.client = settings.MONGODB_CLIENT # An AsyncIOMotorClient
        self.db = self.client[db_name]
        
        self.bucket_name = f"user_{self.user_id}_bucket"
        self.bucket = AsyncGridFSBucket(self.db, bucket_name=self.bucket_name)
        
        self.meta_svc = MetadataService(user_id=user_id)

    async def upload_file_stream(
        self, 
        file_stream: AsyncIterable[bytes], 
        filename: str,
        content_type: str = None
    ) -> str:
        """
        Streams file data directly to GridFS to minimize memory footprint.
        Accepts an async iterable (e.g., from a FastAPI request or Django chunked file).
        """
        # 1. Open an upload stream in GridFS
        grid_in = self.bucket.open_upload_stream(
            filename, 
            metadata={"contentType": content_type, "owner": self.user_id}
        )
        
        try:
            total_size = 0
            # 2. Iterate through incoming chunks and write them immediately
            async for chunk in file_stream:
                await grid_in.write(chunk)
                total_size += len(chunk)
                
            # 3. Finalize the upload
            await grid_in.close()
            file_id_str = str(grid_in._id)

            # 4. Sync with MetadataService
            await self.meta_svc.create_entry(
                file_id=file_id_str,
                filename=filename,
                size=total_size,
                content_type=content_type,
                storage_type="gridfs"
            )
            
            return file_id_str
            
        except Exception as e:
            await grid_in.abort()  # Clean up partial data if upload fails
            raise e


    async def upload_file(self, file_data: bytes, filename: str, content_type: str = None) -> str:
        """
        Uploads a file to GridFS, stores tracking metadata, and returns the file ID.
        """
        # 1. Upload to GridFS
        # Using open_upload_stream allows for setting metadata within GridFS itself
        grid_file_id = await self.bucket.upload_from_stream(
            filename, 
            file_data, 
            metadata={"contentType": content_type, "owner": self.user_id}
        )
        file_id_str = str(grid_file_id)

        # 2. Sync with your MetadataService for high-level tracking
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
        Downloads a file from GridFS using its ID.
        """
        try:
            grid_out = await self.bucket.open_download_stream(ObjectId(file_id))
            return await grid_out.read()
        except Exception as e:
            # Consider using a proper logger here
            print(f"Error downloading file {file_id}: {e}")
            return None

    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves file metadata from the GridFS .files collection.
        """
        cursor = self.bucket.find({"_id": ObjectId(file_id)})
        if await cursor.to_list(length=1):
            file_doc = cursor.delegate.next()
            return {
                "filename": file_doc.filename,
                "upload_date": file_doc.upload_date,
                "length": file_doc.length,
                "metadata": file_doc.metadata
            }
        return None

    async def delete_file(self, file_id: str) -> bool:
        """
        Deletes a file from GridFS and removes its entry from the MetadataService.
        """
        try:
            # 1. Delete from GridFS
            await self.bucket.delete(ObjectId(file_id))
            
            # 2. Delete from MetadataService
            await self.meta_svc.delete_entry(file_id=file_id)
            
            return True
        except Exception as e:
            print(f"Error deleting file {file_id}: {e}")
            return False
