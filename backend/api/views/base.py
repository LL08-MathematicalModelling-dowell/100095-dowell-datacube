"""CRUD operations for documents in a MongoDB collection."""


import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response


class BaseAPIView(APIView):
    """Base API view class to handle common functionality for all API views."""

    @staticmethod
    def handle_errors(fn):
        """
        Decorator to catch exceptions in both sync and async views,
        and return an appropriate DRF Response.
        """
        if asyncio.iscoroutinefunction(fn):
            async def async_wrapper(self, request, *args, **kwargs):
                try:
                    return await fn(self, request, *args, **kwargs)
                except ValueError as e:
                    return Response(
                        {"success": False, "message": f"Value Error: {str(e)}"},
                        status=400
                    )
                except TypeError as e:
                    return Response(
                        {"success": False, "message": f"Type Error: {str(e)}"},
                        status=400
                    )
                except Exception as e:
                    return Response(
                        {"success": False, "message": f"Internal Error: {str(e)}"},
                        status=500
                    )
            return async_wrapper

        # sync path
        def sync_wrapper(self, request, *args, **kwargs):
            try:
                return fn(self, request, *args, **kwargs)
            except ValueError as e:
                return Response(
                    {"success": False, "message": f"Value Error: {str(e)}"},
                    status=400
                )
            except TypeError as e:
                return Response(
                    {"success": False, "message": f"Type Error: {str(e)}"},
                    status=400
                )
            except Exception as e:
                return Response(
                    {"success": False, "message": f"Internal Error: {str(e)}"},
                    status=500
                )
        return sync_wrapper

    def validate_serializer(self, serializer_class, data):
        ser = serializer_class(data=data)
        ser.is_valid(raise_exception=True)
        return ser.validated_data
