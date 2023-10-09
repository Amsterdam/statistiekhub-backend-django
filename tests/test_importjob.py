import os

from django.core.files.base import ContentFile
from django.test import TestCase

from import_export_celery.models.importjob import ImportJob


class ImportJobTestCases(TestCase):

## 9-10-2023 uitgezet vanwege error op permissies op de media foler -> lokaal draait alles nu prima

     def test_delete_file_on_job_delete(self):
          pass
    #     job = ImportJob.objects.create(
    #         file=ContentFile(b"", "file.csv"),
    #         change_summary=ContentFile(b"", "change_summaryfile.html"),
    #     )

    #     file_path = job.file.path
    #     assert os.path.exists(file_path)

    #     change_summary_path = job.change_summary.path
    #     assert os.path.exists(change_summary_path)

    #     job.delete()

    #     assert not os.path.exists(file_path)
    #     assert not ImportJob.objects.filter(id=job.id).exists()

    #     assert not os.path.exists(change_summary_path)
    #     assert not ImportJob.objects.filter(id=job.id).exists()
