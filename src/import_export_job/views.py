import logging
import os

from django.conf import settings
from django.http import Http404, HttpResponse

from main.utils_azure_storage import AzureStorage

logger = logging.getLogger(__name__)

def get_blob(request, blob_name):
    logger.info(f"Requested blob_name: {blob_name}")
    if  hasattr(settings, 'STORAGE_AZURE'):
        try:
            blob_service_client = AzureStorage.get_blob_service_client()
            container_name = settings.STORAGE_AZURE["default"]["OPTIONS"]["azure_container"]
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_data = blob_client.download_blob().readall()

            return HttpResponse(blob_data, content_type="text/html")
        except Exception as e:
            logger.error(f"Error retrieving blob from Azure: {e}")
            raise Http404(f"Bestand {blob_name} niet gevonden")
    else:
        file_path = os.path.join(settings.MEDIA_ROOT, blob_name)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_data = f.read()
            return HttpResponse(file_data, content_type="text/html")
        else:
            raise Http404(f"File {blob_name} niet gevonden in media directory")        
