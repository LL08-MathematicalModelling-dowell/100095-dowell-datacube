from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from api.api_home_data import apis # Make sure your api data is in this file
from django.views.generic import TemplateView


class APIDocsView(APIView):
    """
    Renders the public API documentation page.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Pass the 'apis' data structure to the template
        return render(request, 'api/api_docs.html', {'apis': apis})
    


# class LoginView(TemplateView):
#     template_name = "api/login.html"


class RegisterView(TemplateView):
    template_name = "api/register.html"