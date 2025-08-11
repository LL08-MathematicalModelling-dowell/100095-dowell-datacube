# core/views/page_views.py

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer

from api.services.metadata_service import MetadataService

# This is the key: APIView handles token auth, TemplateHTMLRenderer renders HTML.

# class DashboardBaseView(APIView):
#     """
#     A base view for all dashboard pages. It ensures the user is authenticated
#     via token and then renders an HTML template.
#     """
#     permission_classes = [AllowAny]
#     renderer_classes = [TemplateHTMLRenderer]

#     def get_context_data(self, request, **kwargs):
#         """A helper to provide common context to all dashboard pages."""
#         return {
#             'user': request.user # The MongoUser proxy object
#         }
class DashboardBaseView(APIView):
    """
    A base view for all dashboard pages. It ensures the user is authenticated
    via token and then renders an HTML template.
    """
    permission_classes = [AllowAny]
    renderer_classes = [TemplateHTMLRenderer]

    def get_context_data(self, request, **kwargs):
        """A helper to provide common context to all dashboard pages."""
        return {
            'user': request.user # The MongoUser proxy object
        }


class DashboardOverviewPageView(DashboardBaseView):
    template_name = "dashboard/overview.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        # You can add page-specific data here if needed later
        return render(request, self.template_name, context)

class DashboardAPIKeysPageView(DashboardBaseView):
    template_name = "dashboard/api_keys.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)

class DashboardBillingPageView(DashboardBaseView):
    template_name = "dashboard/billing.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.template_name, context)


class DashboardDatabaseDetailPageView(DashboardBaseView):
    """
    Renders the HTML skeleton for the detailed management page for a single database.
    The actual data will be fetched client-side.
    """
    template_name = "dashboard/database_detail.html"

    def get(self, request, db_id, *args, **kwargs):
        # We still need to pass the db_id to the template so the JavaScript knows which database to fetch.
        context = self.get_context_data(request)
        context['db_id'] = db_id
        return render(request, self.template_name, context)
