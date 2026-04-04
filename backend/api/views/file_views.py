import time

from django.http import Http404, HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from gridfs.grid_file import ObjectId

from api.views.base import BaseAPIView
from api.file_serializer import FileUploadSerializer, FileListQuerySerializer

# Analytics tasks
from analytics.tasks import (
    log_db_operation_task, 
    log_mongo_detail_task, 
    log_slow_query_task
)


class FileListView(BaseAPIView):
    """
    View for listing and uploading files.
    GET returns a paginated list of files with optional search.
    POST allows uploading a new file.
    """
    permission_classes = [IsAuthenticated]

    def _send_file_list_analytics(self, request, total_files, stats, start_time):
        """Helper to send analytics for file listing."""
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Database operation log
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",  # GridFS collection name
            "operation_type": "file_list",
            "document_count": total_files,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        # Mongo detail: total files and storage
        detail_data = {
            "user_id": user_id,
            "returned_documents": total_files,
            "total_files": stats.get("total_count", total_files),
            "total_storage_bytes": stats.get("total_size_bytes", 0),
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        # Slow query detection (threshold 500ms for listing)
        if duration_ms > 500:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "GET",
                    "path": request.path,
                    "params": dict(request.GET.items()),
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 500,
                "collection": "fs.files",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

    def _send_file_upload_analytics(self, request, filename, file_size, file_id, start_time):
        """Helper to send analytics for file upload."""
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Database operation log
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_upload",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        # Mongo detail: file size
        detail_data = {
            "user_id": user_id,
            "inserted_count": 1,
            "file_size_bytes": file_size,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        # Slow upload detection (threshold 2 seconds for uploads)
        if duration_ms > 2000:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "POST",
                    "path": request.path,
                    "filename": filename,
                    "file_size_bytes": file_size,
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 2000,
                "collection": "fs.files",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

    @BaseAPIView.handle_errors
    async def get(self, request):
        start_time = time.perf_counter()
        params = self.validate_serializer(FileListQuerySerializer, request.query_params)
        page = params.get("page", 1)
        page_size = params.get("page_size", 10)
        
        total, files = await self.metadata_svc.list_files_paginated(
            page=page,
            page_size=page_size,
            search_term=params.get("search", "")
        )
        stats = await self.metadata_svc.get_storage_stats()
        
        # Send analytics
        self._send_file_list_analytics(request, total, stats, start_time)
        
        return Response({
            "success": True,
            "data": files,
            "stats": {
                "total_files": stats.get("total_count", total),
                "total_storage_bytes": stats.get("total_size_bytes", 0),
            },
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
            }
        }, status=status.HTTP_200_OK)

    @BaseAPIView.handle_errors
    async def post(self, request):
        start_time = time.perf_counter()
        data = self.validate_serializer(FileUploadSerializer, request.data)
        uploaded_file = data['file']
        
        async def file_chunk_generator():
            for chunk in uploaded_file.chunks():
                yield chunk

        file_id = await self.file_svc.upload_file_stream(
            file_stream=file_chunk_generator(),
            filename=data.get('filename') or uploaded_file.name,
            content_type=data.get('content_type') or uploaded_file.content_type
        )
        
        # Send analytics
        self._send_file_upload_analytics(
            request, 
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_id=file_id,
            start_time=start_time
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
    """View for retrieving file metadata or deleting a file."""
    permission_classes = [IsAuthenticated]

    def _send_file_metadata_analytics(self, request, file_id, start_time):
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_metadata",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        if duration_ms > 500:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "GET",
                    "path": request.path,
                    "file_id": file_id,
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 500,
                "collection": "fs.files",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

    def _send_file_delete_analytics(self, request, file_id, success, start_time):
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_delete",
            "document_count": 1 if success else 0,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {
            "user_id": user_id,
            "deleted_count": 1 if success else 0,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 1000:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "DELETE",
                    "path": request.path,
                    "file_id": file_id,
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 1000,
                "collection": "fs.files",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        start_time = time.perf_counter()
        info = await self.file_svc.get_file_info(file_id)
        if not info:
            raise Http404("File not found")
        self._send_file_metadata_analytics(request, file_id, start_time)
        return Response({"success": True, "info": info})

    @BaseAPIView.handle_errors
    async def delete(self, request, file_id):
        start_time = time.perf_counter()
        success = await self.file_svc.delete_file(file_id)
        if success:
            self._send_file_delete_analytics(request, file_id, success, start_time)
            return Response({"success": True, "message": "File deleted"})
        raise Http404("File not found or unauthorized")


class FileStreamView(BaseAPIView):
    """View for streaming a file. More memory efficient for large files."""
    permission_classes = [IsAuthenticated]

    def _send_file_stream_analytics(self, request, file_id, file_size, start_time):
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_stream",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {
            "user_id": user_id,
            "returned_documents": 1,
            "file_size_bytes": file_size,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        # Streaming threshold higher (3 seconds) as it depends on network
        if duration_ms > 3000:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "GET",
                    "path": request.path,
                    "file_id": file_id,
                    "file_size_bytes": file_size,
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 3000,
                "collection": "fs.files",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        start_time = time.perf_counter()
        try:
            stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
            if stream.metadata.get("user_id") != str(request.user.pk):
                await stream.close()
                return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            raise Http404("File not found")
        
        file_size = stream.length
        self._send_file_stream_analytics(request, file_id, file_size, start_time)

        async def file_content_generator():
            try:
                while True:
                    chunk = await stream.readchunk()
                    if not chunk:
                        break
                    yield chunk
            finally:
                await stream.close()

        response = StreamingHttpResponse(
            file_content_generator(),
            content_type=stream.metadata.get("contentType", "application/octet-stream")
        )
        response['Content-Disposition'] = f'attachment; filename="{stream.filename}"'
        return response


class FileDownloadView(BaseAPIView):
    """
    View for downloading a file (reads entire file into memory).
    Not recommended for large files.
    """
    permission_classes = [IsAuthenticated]

    def _send_file_download_analytics(self, request, file_id, file_size, start_time):
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_download",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore
        
        detail_data = {
            "user_id": user_id,
            "returned_documents": 1,
            "file_size_bytes": file_size,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore
        
        if duration_ms > 3000:  # threshold 3 seconds
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "GET",
                    "path": request.path,
                    "file_id": file_id,
                    "file_size_bytes": file_size,
                },
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 3000,
                "collection": "fs.files",
                "db_id": None,
            }
            log_slow_query_task.delay(slow_data) # type: ignore

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        start_time = time.perf_counter()
        try:
            stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
            if stream.metadata.get("user_id") != str(request.user.pk):
                await stream.close()
                return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            raise Http404("File not found")

        file_size = stream.length
        if file_size > 20 * 1024 * 1024:  # 20MB limit
            await stream.close()
            return Response(
                {"success": False, "error": "FileTooLarge", 
                 "detail": "File exceeds 20MB limit for download"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        file_content = await stream.read()
        await stream.close()
        
        self._send_file_download_analytics(request, file_id, file_size, start_time)

        response = HttpResponse(
            file_content,
            content_type=stream.metadata.get("contentType", "application/octet-stream")
        )
        response['Content-Disposition'] = f'attachment; filename="{stream.filename}"'
        return response



# from django.http import Http404, HttpResponse, StreamingHttpResponse

# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from gridfs.grid_file import ObjectId

# from api.views.base import BaseAPIView
# from api.file_serializer import FileUploadSerializer, FileListQuerySerializer


# class FileListView(BaseAPIView):
#     """
#     View for listing and uploading files.
#     GET returns a paginated list of files with optional search.
#     POST allows uploading a new file.
#     """
#     permission_classes = [IsAuthenticated]


#     @BaseAPIView.handle_errors
#     async def get(self, request):
#         params = self.validate_serializer(FileListQuerySerializer, request.query_params)
#         page = params.get("page", 1)
#         page_size = params.get("page_size", 10)
        
#         # 1. Fetch files and basic total count
#         total, files = await self.metadata_svc.list_files_paginated(
#             page=page,
#             page_size=page_size,
#             search_term=params.get("search", "")
#         )

#         # 2. Get aggregate stats (Total size and count for the user)
#         # Assuming you add a 'get_storage_stats' to your metadata_service
#         stats = await self.metadata_svc.get_storage_stats() 
#         # stats example: {"total_count": 15, "total_size_bytes": 10485760}

#         return Response({
#             "success": True,
#             "data": files,
#             "stats": {
#                 "total_files": stats.get("total_count", total),
#                 "total_storage_bytes": stats.get("total_size_bytes", 0),
#             },
#             "pagination": {
#                 "current_page": page,
#                 "page_size": page_size,
#                 "total_items": total,
#                 "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
#             }
#         }, status=status.HTTP_200_OK)

#     @BaseAPIView.handle_errors
#     async def post(self, request):
#         data = self.validate_serializer(FileUploadSerializer, request.data)
#         uploaded_file = data['file']
        
#         async def file_chunk_generator():
#             for chunk in uploaded_file.chunks(): yield chunk

#         file_id = await self.file_svc.upload_file_stream(
#             file_stream=file_chunk_generator(),
#             filename=data.get('filename') or uploaded_file.name,
#             content_type=data.get('content_type') or uploaded_file.content_type
#         )
#         return Response(
#             {
#                 "success": True, "file_id": file_id,
#                 "filename": uploaded_file.name,
#                 "file_size": uploaded_file.size
#             },
#             status=status.HTTP_201_CREATED
#         )

# class FileDetailView(BaseAPIView):
#     """View for retrieving file metadata or deleting a file."""
#     permission_classes = [IsAuthenticated]

#     @BaseAPIView.handle_errors
#     async def get(self, request, file_id):
#         info = await self.file_svc.get_file_info(file_id)
#         if not info: raise Http404("File not found")
#         return Response({"success": True, "info": info})

#     @BaseAPIView.handle_errors
#     async def delete(self, request, file_id):
#         if await self.file_svc.delete_file(file_id):
#             return Response({"success": True, "message": "File deleted"})
#         raise Http404("File not found or unauthorized")

# class FileStreamView(BaseAPIView):
#     """View for streaming a file. This is more memory efficient for large files."""
#     permission_classes = [IsAuthenticated]

#     @BaseAPIView.handle_errors
#     async def get(self, request, file_id):
#         try:
#             # Check ownership via the bucket find query in the driver
#             stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
#             # Security: Verify ownership from stream metadata
#             if stream.metadata.get("user_id") != str(request.user.pk): # type: ignore
#                 await stream.close()
#                 return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
#         except Exception: raise Http404("File not found")

#         async def file_content_generator():
#             try:
#                 while True:
#                     # Using readchunk() to read the next chunk of data from the stream. 
#                     # + This is more efficient for large files.
#                     chunk = await stream.readchunk()  # type: ignore
#                     if not chunk: break
#                     yield chunk
#             finally: await stream.close()

#         response = StreamingHttpResponse(
#             file_content_generator(),
#             content_type=stream.metadata.get("contentType", "application/octet-stream") # type: ignore
#             )
#         response['Content-Disposition'] = f'attachment; filename="{stream.filename}"'
#         return response


# class FileDownloadView(BaseAPIView):
#     """
#     View for downloading a file. This is a simpler version 
#     that reads the entire file into memory before sending. 
#     Not recommended for large files.
#     """

#     permission_classes = [IsAuthenticated]

#     @BaseAPIView.handle_errors
#     async def get(self, request, file_id):
#         try:
#             # Check ownership via the bucket find query in the driver
#             stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
#             # Security: Verify ownership from stream metadata
#             if stream.metadata.get("user_id") != str(request.user.pk): # type: ignore
#                 await stream.close()
#                 return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
#         except Exception: raise Http404("File not found")

#         # check file size before reading into memory (optional but recommended)
#         file_size = stream.length  # type: ignore
#         if file_size > 20 * 1024 * 1024:  # 20MB limit for in-memory download
#             await stream.close()
#             return Response({"success": False, "error": "FileTooLarge", "detail": "File exceeds 20MB limit for download"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

#         file_content = await stream.read()
#         await stream.close()

#         response = HttpResponse(
#             file_content,
#             content_type=stream.metadata.get("contentType", "application/octet-stream") # type: ignore
#         )
#         response['Content-Disposition'] = f'attachment; filename="{stream.filename}"'
#         return response

    