import asyncio
from functools import wraps
from typing import Any, Callable, Type, Dict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer

class BaseAPIView(APIView):
    """
    Enhanced Base API View for MongoDB-backed DRF services.
    Provides automated error handling and standardized serializer validation.
    """

    @staticmethod
    def handle_errors(fn: Callable) -> Callable:
        """
        A universal decorator for sync and async views that catches common 
        errors and returns standard DRF responses.
        """
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(self, request, *args, **kwargs):
                try:
                    return await fn(self, request, *args, **kwargs)
                except (ValueError, TypeError) as e:
                    return Response(
                        {"success": False, "error": "Validation Error", "detail": str(e)}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                except Exception as e:
                    # In production, use structured logging here
                    return Response(
                        {"success": False, "error": "Internal Server Error", "detail": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            return async_wrapper

        @wraps(fn)
        def sync_wrapper(self, request, *args, **kwargs):
            try:
                return fn(self, request, *args, **kwargs)
            except (ValueError, TypeError) as e:
                return Response(
                    {"success": False, "error": "Validation Error", "detail": str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"success": False, "error": "Internal Server Error", "detail": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return sync_wrapper

    def validate_serializer(self, serializer_class: Type[Serializer], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardizes the validation of incoming data against a DRF serializer.
        """
        serializer = serializer_class(data=data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data # type: ignore









# """CRUD operations for documents in a MongoDB collection."""

# import asyncio
# from rest_framework.views import APIView
# from rest_framework.response import Response


# class BaseAPIView(APIView):
#     """Base API view class to handle common functionality for all API views."""

#     @staticmethod
#     def handle_errors(fn):
#         """
#         Decorator to catch exceptions in both sync and async views,
#         and return an appropriate DRF Response.
#         """
#         if asyncio.iscoroutinefunction(fn):
#             async def async_wrapper(self, request, *args, **kwargs):
#                 try:
#                     return await fn(self, request, *args, **kwargs)
#                 except ValueError as e:
#                     return Response(
#                         {"success": False, "message": f"Value Error: {str(e)}"},
#                         status=400
#                     )
#                 except TypeError as e:
#                     return Response(
#                         {"success": False, "message": f"Type Error: {str(e)}"},
#                         status=400
#                     )
#                 except Exception as e:
#                     return Response(
#                         {"success": False, "message": f"Internal Error: {str(e)}"},
#                         status=500
#                     )
#             return async_wrapper

#         # sync path
#         def sync_wrapper(self, request, *args, **kwargs):
#             try:
#                 return fn(self, request, *args, **kwargs)
#             except ValueError as e:
#                 return Response(
#                     {"success": False, "message": f"Value Error: {str(e)}"},
#                     status=400
#                 )
#             except TypeError as e:
#                 return Response(
#                     {"success": False, "message": f"Type Error: {str(e)}"},
#                     status=400
#                 )
#             except Exception as e:
#                 return Response(
#                     {"success": False, "message": f"Internal Error: {str(e)}"},
#                     status=500
#                 )
#         return sync_wrapper

#     def validate_serializer(self, serializer_class, data):
#         ser = serializer_class(data=data)
#         ser.is_valid(raise_exception=True)
#         return ser.validated_data
