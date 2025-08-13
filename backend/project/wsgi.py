"""
WSGI config for the DataCube project.
"""
import os
from django.core.wsgi import get_wsgi_application

# IMPORTANT: This should point to your PRODUCTION settings.
# Your hosting provider will use this file.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.production')

application = get_wsgi_application()
