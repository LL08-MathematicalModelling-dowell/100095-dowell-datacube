from rest_framework.views import APIView
from rest_framework.response import Response

class BaseAPIView(APIView):
    """Base API view class to handle common functionality for all API views."""
    @staticmethod
    def handle_errors(fn):
        """Decorator to handle errors in API views."""
        def wrapper(self, request, *args, **kw):
            try:
                return fn(self, request, *args, **kw)
            except ValueError as e:
                return Response({"success": False,"message": f"Value Error: {str(e)}"}, status=400)
            except Exception as e:
                return Response({"success": False,"message": f"Internal error : {str(e)}"}, status=500)
        return wrapper

    def validate_serializer(self, serializer_class, data):
        """Validate the data using the provided serializer class."""
        ser = serializer_class(data=data)
        ser.is_valid(raise_exception=True)
        return ser.validated_data