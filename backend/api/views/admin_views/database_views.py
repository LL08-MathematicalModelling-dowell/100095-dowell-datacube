from rest_framework.response import Response
from api.views.base import BaseAPIView
from api.permissions import IsAdminUserOrInternalIP
from api.services.metadata_service import MetadataService


class PruneFieldsView(BaseAPIView):
    permission_classes = [IsAdminUserOrInternalIP]

    @BaseAPIView.handle_errors
    async def post(self, request):
        db_id = request.data["database_id"]
        dry_run = request.data.get("dry_run", True)
        result = await MetadataService(user_id=request.user.id).prune_inactive_fields(
            db_id=db_id,
            dry_run=dry_run
        )
        return Response(result, status=200)