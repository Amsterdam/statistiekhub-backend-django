import shutil
import tempfile

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage, default_storage
from django.urls import reverse
from model_bakery import baker

from import_export_job.models.importjob import ImportJob


# because problem with writepermission when no azurestorage
@pytest.fixture(scope='function', autouse=True)
def temporary_media_root():
    """ Fixture for temp media dir """
    temp_media = tempfile.mkdtemp()
    settings.MEDIA_ROOT = temp_media
    yield
    shutil.rmtree(temp_media)


@pytest.mark.django_db
def test_blob_link(client):
    """ test the get_blob url """
    job = ImportJob(file='test.json')

    test_html = "<html><body><h1>Change Summary</h1></body></html>"
    test_file = ContentFile(test_html.encode('utf-8'), name='test.html')
    job.change_summary.save('test.html', test_file)
    
    assert (default_storage.exists(job.change_summary.name))

    url = reverse('get_blob', args=[job.change_summary])
    response = client.get(url)
    assert response.status_code == 200

    print(response.content)
    assert b"<html>" in response.content