import os

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from model_bakery import baker

from import_export_job.models import ImportJob
from import_export_job.tasks import _run_import_job, get_format
from tests.temp_storage import temporary_media_root


class MockFormat:
    CONTENT_TYPE = "mock/type"

    def __call__(self):
        return self


@pytest.fixture
def mock_default_formats(monkeypatch):
    from import_export_job import tasks

    monkeypatch.setattr(
        tasks,
        "DEFAULT_FORMATS",
        [
            MockFormat(),
        ],
    )


def get_test_import_observation_file_content():
    headers = '"spatial_code";"spatial_type";"spatial_date";"temporal_date";"temporal_type";"measure";"value"'
    data = '"0363";"Gemeente";20220324;20231001;"peildatum";"OSCHVO";84'

    content = f"{headers}\n{data}"
    return content.encode("utf-8")


@pytest.mark.django_db
def test_get_format(mock_default_formats):

    job = baker.make(ImportJob, format="mock/type")

    result = get_format(job)
    assert isinstance(result, MockFormat)

    job.delete()
    assert len(ImportJob.objects.all()) == 0


@pytest.mark.django_db
def test_delete_file_on_job_delete(temporary_media_root):
    job = baker.make(
        ImportJob,
        format="semicolon text/csv",
        model="Observation",
        file=ContentFile(get_test_import_observation_file_content(), "mock_file1.csv"),
    )
    file_path = job.file.path
    assert os.path.exists(file_path)

    _run_import_job(job, dry_run=True)

    summary_path = job.change_summary.path
    assert os.path.exists(summary_path)

    job.delete()

    assert not os.path.exists(file_path)
    assert not os.path.exists(summary_path)
    assert not ImportJob.objects.filter(id=job.id).exists()
    assert len(ImportJob.objects.all()) == 0


@pytest.mark.django_db
def test_run_import_job(temporary_media_root):
    import_job = baker.make(
        ImportJob,
        format="semicolon text/csv",
        model="Observation",
        file=ContentFile(get_test_import_observation_file_content(), "mock_file2.csv"),
    )
    assert os.path.exists(import_job.file.path)

    _run_import_job(import_job, dry_run=True)

    assert import_job.errors == "ERRORS zie change_summary"
    assert (
        import_job.change_summary.name
        == "django-import-job-change-summaries/mock_file2.csv.html"
    )

    import_job.delete()
