from gridfs.grid_file import ObjectId
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import Http404, StreamingHttpResponse
from api.views.base import BaseAPIView
from api.file_serializer import FileUploadSerializer, FileListQuerySerializer


class FileListView(BaseAPIView):
    """
    View for listing and uploading files.
    GET returns a paginated list of files with optional search.
    POST allows uploading a new file.
    """
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    async def get(self, request):
        params = self.validate_serializer(FileListQuerySerializer, request.query_params)
        total, files = await self.metadata_svc.list_files_paginated(
            page=params.get("page", 1),
            page_size=params.get("page_size", 50),
            search_term=params.get("search", "")
        )
        return Response({
            "success": True,
            "data": files,
            "pagination": {"total": total}},
            status=status.HTTP_200_OK
        )

    @BaseAPIView.handle_errors
    async def post(self, request):
        data = self.validate_serializer(FileUploadSerializer, request.data)
        uploaded_file = data['file']
        
        async def file_chunk_generator():
            for chunk in uploaded_file.chunks(): yield chunk

        file_id = await self.file_svc.upload_file_stream(
            file_stream=file_chunk_generator(),
            filename=data.get('filename') or uploaded_file.name,
            content_type=data.get('content_type') or uploaded_file.content_type
        )
        return Response(
            {
                "success": True, "file_id": file_id,
                "filename": uploaded_file.name,
                "file_size": uploaded_file.size
            },
            status=status.HTTP_201_CREATED
        )

class FileDetailView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        info = await self.file_svc.get_file_info(file_id)
        if not info: raise Http404("File not found")
        return Response({"success": True, "info": info})

    @BaseAPIView.handle_errors
    async def delete(self, request, file_id):
        if await self.file_svc.delete_file(file_id):
            return Response({"success": True, "message": "File deleted"})
        raise Http404("File not found or unauthorized")

class FileDownloadView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        try:
            # Check ownership via the bucket find query in the driver
            stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
            # Security: Verify ownership from stream metadata
            if stream.metadata.get("user_id") != str(request.user.pk): # type: ignore
                await stream.close()
                return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
        except Exception: raise Http404("File not found")

        async def file_content_generator():
            try:
                while True:
                    chunk = await stream.read(65536)
                    if not chunk: break
                    yield chunk
            finally: await stream.close()

        response = StreamingHttpResponse(
            file_content_generator(),
            content_type=stream.metadata.get("contentType", "application/octet-stream") # type: ignore
            )
        response['Content-Disposition'] = f'attachment; filename="{stream.filename}"'
        return response
