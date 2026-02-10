import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from model_bakery import baker

from import_export_job.models import ImportJob
from import_export_job.tasks import _run_import_job, get_format
from tests.temp_storage import temporary_media_root  # noqa: F401


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
def test_delete_file_on_job_delete():
    job = baker.make(
        ImportJob,
        format="semicolon text/csv",
        model="Observation",
        file=ContentFile(get_test_import_observation_file_content(), "mock_file1.csv"),
    )

    file_name = job.file.name
    assert default_storage.exists(file_name)

    _run_import_job(job, dry_run=True)

    summary_name = job.change_summary.name
    assert default_storage.exists(summary_name)

    job.delete()

    assert not default_storage.exists(file_name)
    assert not default_storage.exists(summary_name)
    assert not ImportJob.objects.filter(id=job.id).exists()
    assert len(ImportJob.objects.all()) == 0


@pytest.mark.django_db
def test_run_import_job(temporary_media_root):  # noqa: F811
    import_job = baker.make(
        ImportJob,
        format="semicolon text/csv",
        model="Observation",
        file=ContentFile(get_test_import_observation_file_content(), "mock_file2.csv"),
    )
    assert default_storage.exists(import_job.file.name)

    _run_import_job(import_job, dry_run=True)

    assert import_job.errors == "ERRORS zie change_summary"
    assert import_job.change_summary.name == "django-import-job-change-summaries/mock_file2.csv.html"

    import_job.delete()
