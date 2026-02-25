import asyncio
from django.conf import settings
from gridfs.grid_file import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404

from api.views.base import BaseAPIView
from api.file_serializer import (
    FileUploadSerializer,
    FileListQuerySerializer,
    FileDeleteSerializer,
)
from api.services.metadata_service import MetadataService
from api.services.gridfs_service import GridFSService


class FileListView(BaseAPIView):
    """
    List all files for the authenticated user, or upload a new file.
    """
    permission_classes = [IsAuthenticated]

    @property
    def file_svc(self):
        # GridFS bucket lives in a dedicated database (set in settings)
        return GridFSService(
            db_name=settings.FILE_STORAGE_DB_NAME,
            user_id=str(self.request.user.pk)
        )

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request):
        """Paginated list of file metadata."""
        params = self.validate_serializer(FileListQuerySerializer, request.query_params)
        page = params.get("page", 1)
        page_size = params.get("page_size", 50)
        search = params.get("search", "")

        total, files = await self.metadata_svc.list_files_paginated(
            page=page, page_size=page_size, search_term=search
        )

        return Response({
            "success": True,
            "data": files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        }, status=status.HTTP_200_OK)

    @BaseAPIView.handle_errors
    async def post(self, request):
        """Upload a new file (multipart form)."""
        # 1. Validate input
        data = self.validate_serializer(FileUploadSerializer, request.data)
        uploaded_file = data['file']
        filename = data.get('filename') or uploaded_file.name
        content_type = data.get('content_type') or uploaded_file.content_type


        # 2. Quota check
        if await self.metadata_svc.check_quota_is_exceeded():
            return Response(
                {"success": False, "message": "Storage quota exceeded."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Stream the file to GridFS
        # Convert the Django uploaded file into an async iterable of bytes
        async def file_chunk_generator():
            # Read in chunks of 1MB (default chunk size of GridFSService)
            chunk_size = 1024 * 1024
            while True:
                # run_in_executor because .read() is blocking
                chunk = await asyncio.to_thread(uploaded_file.read, chunk_size)
                if not chunk:
                    break
                yield chunk

        file_id = await self.file_svc.upload_file_stream(
            file_stream=file_chunk_generator(),
            filename=filename,
            content_type=content_type
            # progress_callback can be omitted here
        )

        # 4. Return the new file's ID
        return Response({
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "size": uploaded_file.size,
        }, status=status.HTTP_201_CREATED)


class FileDetailView(BaseAPIView):
    """
    Retrieve metadata or delete a specific file.
    URL: /api/files/<file_id>/
    """
    permission_classes = [IsAuthenticated]

    @property
    def file_svc(self):
        return GridFSService(
            db_name=settings.FILE_STORAGE_DB_NAME,
            user_id=str(self.request.user.pk)
        )

    @property
    def metadata_svc(self):
        return MetadataService(user_id=str(self.request.user.pk))

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        """Retrieve file metadata (from GridFS .files collection)."""
        info = await self.file_svc.get_file_info(file_id)
        if info is None:
            raise Http404("File not found")
        # Combine with our own metadata if desired
        own_meta = await self.metadata_svc.get_file_entry(file_id)
        return Response({
            "success": True,
            "file_id": file_id,
            "gridfs_info": info,
            "metadata": own_meta   # includes user_id, uploaded_at, etc.
        })

    @BaseAPIView.handle_errors
    async def delete(self, request, file_id):
        """Delete a file (both GridFS and metadata)."""
        # Validate (optional: could use a serializer for body data)
        success = await self.file_svc.delete_file(file_id)
        if not success:
            return Response(
                {"success": False, "message": "File not found or deletion failed."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({"success": True, "message": "File deleted."})


class FileDownloadView(BaseAPIView):
    """
    Stream the actual file content.
    URL: /api/files/<file_id>/download/
    """
    permission_classes = [IsAuthenticated]

    @property
    def file_svc(self):
        return GridFSService(
            db_name=settings.FILE_STORAGE_DB_NAME,
            user_id=str(self.request.user.pk)
        )

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        """Download the file as an attachment."""
        try:
            # Get the GridFS stream
            stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
            # Create a FileResponse that streams the content
            response = FileResponse(
                stream,  # stream is an async generator; FileResponse expects a file-like
                as_attachment=True,
                filename=stream.filename
            )
            # Set content-type if available in metadata
            if stream.metadata and stream.metadata.get("contentType"):
                response["Content-Type"] = stream.metadata["contentType"]
            return response
        except Exception:
            raise Http404("File not found")