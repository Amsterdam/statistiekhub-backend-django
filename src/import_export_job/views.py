import logging

from django.core.files.storage import default_storage
from django.http import FileResponse, Http404

logger = logging.getLogger(__name__)


def get_blob(request, blob_name):
    if not default_storage.exists(blob_name):
        raise Http404(f"Bestand {blob_name} niet gevonden")

    file_obj = default_storage.open(blob_name, "rb")
    return FileResponse(file_obj)
