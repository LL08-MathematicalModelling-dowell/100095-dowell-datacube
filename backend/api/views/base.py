"""CRUD operations for documents in a MongoDB collection."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, ParseError
from django.core.exceptions import ObjectDoesNotExist
import logging

# logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """Base API view with standardized error handling and validation."""

    @staticmethod
    def handle_errors(fn):
        """Decorator to handle errors in API views gracefully."""
        async def wrapper(self, request, *args, **kwargs):
            try:
                return await fn(self, request, *args, **kwargs)
            except ValidationError as e:
                return Response({"success": False, "message": f"Validation error", "errors": e.detail}, status=400)
            except ParseError as e:
                return Response({"success": False, "message": f"Parse error: {str(e)}"}, status=400)
            except ObjectDoesNotExist as e:
                return Response({"success": False, "message": f"Not found: {str(e)}"}, status=404)
            except ValueError as e:
                return Response({"success": False, "message": f"Value error: {str(e)}"}, status=400)
            except TypeError as e:
                return Response({"success": False, "message": f"Type error: {str(e)}"}, status=400)
            except Exception as e:
                # logger.exception("Unhandled exception in view")
                return Response({"success": False, "message": f"Internal server error: {str(e)}"}, status=500)
        return wrapper

    def validate_serializer(self, serializer_class, data):
        """Validate request data with serializer, return validated fields only."""
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
