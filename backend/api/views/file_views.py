import time

from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from gridfs.grid_file import ObjectId

from api.views.base import BaseAPIView
from api.file_serializer import FileUploadSerializer, FileListQuerySerializer
from api.utils.signing import generate_signed_url, verify_signed_url

# Analytics tasks
from analytics.tasks import (
    log_db_operation_task, 
    log_mongo_detail_task, 
    log_slow_query_task
)


class FileListView(BaseAPIView):
    """
    View for listing and uploading files.
    GET returns a paginated list of files with signed URLs.
    POST allows uploading a new file.
    """
    permission_classes = [IsAuthenticated]

    def _send_file_list_analytics(self, request, total_files, stats, start_time):
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000

        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_list",
            "document_count": total_files,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore

        detail_data = {
            "user_id": user_id,
            "returned_documents": total_files,
            "total_files": stats.get("total_count", total_files),
            "total_storage_bytes": stats.get("total_size_bytes", 0),
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore

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
        user_id = str(request.user.pk)
        duration_ms = (time.perf_counter() - start_time) * 1000

        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_upload",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data) # type: ignore

        detail_data = {
            "user_id": user_id,
            "inserted_count": 1,
            "file_size_bytes": file_size,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore

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

        # Fetch files and stats
        total, files = await self.metadata_svc.list_files_paginated(
            page=page,
            page_size=page_size,
            search_term=params.get("search", "")
        )
        stats = await self.metadata_svc.get_storage_stats()

        # Generate signed URLs for each file
        user_id = str(request.user.pk)
        for file_entry in files:
            file_id = str(file_entry.get("file_id"))
            file_entry["signed_url"] = generate_signed_url(
                file_id=file_id,
                user_id=user_id,
                expires_in_seconds=60 * 60 * 5  # 5 hours
            )

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

        # Return the signed URL for the newly uploaded file as well
        signed_url = generate_signed_url(
            file_id=file_id,
            user_id=str(request.user.pk),
            expires_in_seconds=60 * 60 * 5  # 5 hours
        )

        return Response(
            {
                "success": True,
                "file_id": file_id,
                "filename": uploaded_file.name,
                "file_size": uploaded_file.size,
                "signed_url": signed_url
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
            return Response({"success": False, "message": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        # Add signed URL to metadata
        file_id = str(info.get("file_id")) 
        user_id = str(request.user.pk)
        info["signed_url"] = generate_signed_url(
            file_id=file_id,
            user_id=user_id,
            expires_in_seconds=60 * 60 * 24 # 24 hours
        )

        self._send_file_metadata_analytics(request, file_id, start_time)
        return Response({"success": True, "info": info})

    @BaseAPIView.handle_errors
    async def delete(self, request, file_id):
        start_time = time.perf_counter()
        success = await self.file_svc.delete_file(file_id)
        if success:
            self._send_file_delete_analytics(request, file_id, success, start_time)
            return Response({"success": True, "message": "File deleted"}, status=status.HTTP_200_OK)
        return Response({"success": False, "message": "File not found"}, status=status.HTTP_404_NOT_FOUND)


class FileStreamView(BaseAPIView):
    """
    Stream a file using a signed URL (no JWT/api_key required in query).
    Supports HTTP range requests (seeking) and partial content (206).
    """
    # Disable DRF authentication – we validate the signed URL ourselves
    permission_classes = []
    authentication_classes = []

    def _send_file_stream_analytics(self, request, file_id, file_size, start_time, bytes_sent=None, user_id=None):
        """Send analytics for the stream operation."""
        duration_ms = (time.perf_counter() - start_time) * 1000
        # user_id is passed from validation (owner of the file)
        if not user_id:
            return

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
            "bytes_sent": bytes_sent if bytes_sent else file_size,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore

        if duration_ms > 3000:
            slow_data = {
                "user_id": user_id,
                "query_details": {
                    "method": "GET",
                    "path": request.path,
                    "file_id": file_id,
                    "file_size_bytes": file_size,
                    "range": request.headers.get('Range', 'none'),
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

        # ----- Signed URL validation -----
        expires = request.GET.get('expires')
        signature = request.GET.get('sig')
        if not expires or not signature:
            return Response(
                {"success": False, "detail": "Missing signature parameters."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            expires_int = int(expires)
        except ValueError:
            return Response(
                {"success": False, "detail": "Invalid expiration."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2. Get the "System" bucket (unscoped) to find out who owns this file
        from gridfs.asynchronous import AsyncGridFSBucket # type: ignore

        
        client = settings.MONGODB_CLIENT
        db = client[settings.FILE_STORAGE_DB_NAME]
        system_bucket = AsyncGridFSBucket(db, bucket_name="user_storage")

        try:
            # We use find_one to get metadata without opening a full stream yet
            file_doc = system_bucket.find({"_id": ObjectId(file_id)}).limit(1)
            if not file_doc:
                raise Http404("File not found")
            
            file_doc = await file_doc.to_list()
            if not file_doc or len(file_doc) == 0:
                raise Http404("File not found")
            
            owner_id = file_doc[0].metadata.get("user_id")
        except Exception as e:
            raise Http404(f"Error fetching file metadata for streaming: {e}")

        # 3. Validate Signature with the owner_id we just found
        if not verify_signed_url(file_id, owner_id, int(expires), signature):
            return Response({"detail": "Invalid/Expired signature"}, status=401)

        # 4. Success! Now set the ID so self.file_svc works
        self._forced_user_id = owner_id

        # ----- Proceed with streaming -----
        try:
            stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
            # Double‑check ownership (optional, already validated by signature)
            if stream.metadata.get("user_id") != owner_id:
                await stream.close()
                return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            raise Http404("File not found")

        file_size = stream.length
        content_type = stream.metadata.get("contentType", "application/octet-stream")
        filename = stream.filename

        # ----- Range request handling (seeking support) -----
        range_header = request.headers.get('Range', '').strip()
        status_code = 200
        start_byte = 0
        end_byte = file_size - 1
        content_length = file_size
        content_range = None

        if range_header and range_header.startswith('bytes='):
            try:
                range_value = range_header[6:]  # Remove "bytes="
                if ',' not in range_value:  # Single range only
                    parts = range_value.split('-')
                    if parts[0]:
                        start_byte = int(parts[0])
                    if len(parts) > 1 and parts[1]:
                        end_byte = int(parts[1])
                    else:
                        end_byte = file_size - 1

                    if start_byte >= file_size or end_byte >= file_size or start_byte > end_byte:
                        await stream.close()
                        return Response(
                            {"error": "Requested range not satisfiable"},
                            status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                            headers={'Content-Range': f'bytes */{file_size}'}
                        )

                    content_length = end_byte - start_byte + 1
                    status_code = 206
                    content_range = f'bytes {start_byte}-{end_byte}/{file_size}'
            except (ValueError, IndexError):
                # Malformed range – serve full file
                pass

        # ----- Response headers -----
        headers = {
            'Content-Type': content_type,
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Accept-Ranges': 'bytes',
        }
        if status_code == 206:
            headers['Content-Range'] = content_range
            headers['Content-Length'] = str(content_length)
        else:
            headers['Content-Length'] = str(file_size)

        # ----- Async generator for streaming the requested byte range -----
        async def file_content_generator():
            bytes_sent = 0
            try:
                bytes_remaining = content_length
                # Seek to start_byte by consuming chunks
                if start_byte > 0:
                    bytes_to_skip = start_byte
                    while bytes_to_skip > 0:
                        chunk = await stream.readchunk()
                        if not chunk:
                            break
                        chunk_len = len(chunk)
                        if chunk_len <= bytes_to_skip:
                            bytes_to_skip -= chunk_len
                        else:
                            # Part of this chunk is needed
                            needed_start = bytes_to_skip
                            yield chunk[needed_start:]
                            bytes_remaining -= (chunk_len - needed_start)
                            bytes_sent += (chunk_len - needed_start)
                            bytes_to_skip = 0
                            break
                # Send remaining chunks up to content_length
                while bytes_remaining > 0:
                    chunk = await stream.readchunk()
                    if not chunk:
                        break
                    if len(chunk) > bytes_remaining:
                        chunk = chunk[:bytes_remaining]
                    yield chunk
                    bytes_remaining -= len(chunk)
                    bytes_sent += len(chunk)
            finally:
                await stream.close()
                # Send analytics after streaming completes
                self._send_file_stream_analytics(
                    request, file_id, file_size, start_time,
                    bytes_sent=bytes_sent, user_id=owner_id
                )

        return StreamingHttpResponse(
            file_content_generator(),
            status=status_code,
            headers=headers,
        )


class FileDownloadView(BaseAPIView):
    """
    Download a small file (≤20MB) using a signed URL.
    Reads entire file into memory – NOT suitable for large files.
    For streaming/large files, use FileStreamView.
    """
    permission_classes = []          # No DRF auth – we validate signed URL
    authentication_classes = []

    def _send_file_download_analytics(self, request, file_id, file_size, start_time, user_id=None):
        duration_ms = (time.perf_counter() - start_time) * 1000
        if not user_id:
            return

        db_op_data = {
            "user_id": user_id,
            "db_id": None,
            "collection": "fs.files",
            "operation_type": "file_download",
            "document_count": 1,
            "query_complexity": "simple",
        }
        log_db_operation_task.delay(db_op_data)  # type: ignore

        detail_data = {
            "user_id": user_id,
            "returned_documents": 1,
            "file_size_bytes": file_size,
        }
        log_mongo_detail_task.delay(detail_data) # type: ignore  

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
            log_slow_query_task.delay(slow_data)  # type: ignore 

    @BaseAPIView.handle_errors
    async def get(self, request, file_id):
        start_time = time.perf_counter()

        # ----- Signed URL validation -----
        expires = request.GET.get('expires')
        signature = request.GET.get('sig')
        if not expires or not signature:
            return Response(
                {"success": False, "detail": "Missing signature parameters."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            expires_int = int(expires)
        except ValueError:
            return Response(
                {"success": False, "detail": "Invalid expiration."},
                status=status.HTTP_401_UNAUTHORIZED
            )


        # 2. Get the "System" bucket (unscoped) to find out who owns this file
        from gridfs.asynchronous import AsyncGridFSBucket # type: ignore

        
        client = settings.MONGODB_CLIENT
        db = client[settings.FILE_STORAGE_DB_NAME]
        system_bucket = AsyncGridFSBucket(db, bucket_name="user_storage")

        try:
            # We use find_one to get metadata without opening a full stream yet
            file_doc = system_bucket.find({"_id": ObjectId(file_id)}).limit(1)
            if not file_doc:
                raise Http404("File not found")
            
            file_doc = await file_doc.to_list()
            if not file_doc or len(file_doc) == 0:
                raise Http404("File not found")
            
            owner_id = file_doc[0].metadata.get("user_id")
        except Exception as e:
            raise Http404(f"Error fetching file metadata for download: {e}")

        # 3. Validate Signature with the owner_id we just found
        if not verify_signed_url(file_id, owner_id, int(expires), signature):
            return Response({"detail": "Invalid/Expired signature"}, status=401)

        # 4. Success! Now set the ID so self.file_svc works
        self._forced_user_id = owner_id

        # ----- Read file (in‑memory) -----
        try:
            stream = await self.file_svc.bucket.open_download_stream(ObjectId(file_id))
            # Ownership double‑check (optional)
            if stream.metadata.get("user_id") != owner_id:
                await stream.close()
                return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            raise Http404("File not found")

        file_size = stream.length
        if file_size > 20 * 1024 * 1024:  # 20MB limit
            await stream.close()
            return Response(
                {"success": False, "error": "FileTooLarge",
                 "detail": "File exceeds 20MB limit for download. Use /stream/ endpoint."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        file_content = await stream.read()
        await stream.close()

        content_type = stream.metadata.get("contentType", "application/octet-stream")
        filename = stream.filename

        # Send analytics
        self._send_file_download_analytics(request, file_id, file_size, start_time, user_id=owner_id)

        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
