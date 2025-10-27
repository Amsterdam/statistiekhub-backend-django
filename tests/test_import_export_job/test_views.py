import os

import pytest
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.urls import reverse
from model_bakery import baker

from import_export_job.models.importjob import ImportJob
from tests.temp_storage import temporary_media_root


@pytest.mark.django_db
def test_blob_link(client, temporary_media_root):
    """test the get_blob url"""
    creator = baker.make(User)
    job = ImportJob(file="test.json", created_by=creator)

    test_html = "<html><body><h1>Change Summary</h1></body></html>"
    test_file = ContentFile(test_html.encode("utf-8"), name="test.html")
    job.change_summary.save("test.html", test_file)

    assert os.path.exists(job.change_summary.path)

    url = reverse("get_blob", args=[job.change_summary.path])
    response = client.get(url)
    assert response.status_code == 200

    retrieved_content = b"".join(response.streaming_content)
    assert b"<html>" in retrieved_content
