# Author: Timothy Hobbs <timothy <at> hobbs.cz>
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import models
from .model_config import ModelConfig
from .utils import DEFAULT_FORMATS

logger = logging.getLogger(__name__)


importables = getattr(settings, "IMPORT_EXPORT_JOB_MODELS", {})


def change_job_status(job, direction, job_status, dry_run=False):
    if dry_run:
        job_status = "[Dry run] " + job_status
    else:
        job_status = job_status
    cache.set(direction + "_job_status_%s" % job.pk, job_status)
    job.job_status = job_status
    job.save()


def get_format(job):
    for format in DEFAULT_FORMATS:
        if job.format == format.CONTENT_TYPE:
            return format()
            break


def _run_import_job(import_job, dry_run=True):
    change_job_status(import_job, "import", "1/5 Import started", dry_run)
    import_job.errors = ""

    model_config = ModelConfig(**importables[import_job.model])

    import_format = get_format(import_job)

    # Copied from https://github.com/django-import-export/django-import-export/blob/3c082f98afe7996e79f936418fced3094f141c26/import_export/admin.py#L260 sorry  # noqa
    try:
        data = import_job.file.read()

        if isinstance(data, bytes):
            data = data.decode("utf8")

        dataset = import_format.create_dataset(data)

    except UnicodeDecodeError as e:
        import_job.errors += _("Imported file has a wrong encoding: %s" % e) + "\n"
        change_job_status(
            import_job, "import", "Imported file has a wrong encoding", dry_run
        )
        import_job.save()
        return

    except Exception as e:
        import_job.errors += _("Error reading file: %s") % e + "\n"
        change_job_status(import_job, "import", "Error reading file", dry_run)
        import_job.save()
        return

    change_job_status(import_job, "import", "2/5 Processing import data", dry_run)

    class Resource(model_config.resource):
        def __init__(self, import_job, *args, **kwargs):
            self.import_job = import_job
            super().__init__(*args, **kwargs)

        def before_import_row(self, row, **kwargs):
            if "row_number" in kwargs:
                row_number = kwargs["row_number"]
                if row_number % 100 == 0 or row_number == 1:
                    change_job_status(
                        import_job,
                        "import",
                        f"3/5 Importing row {row_number}/{len(dataset)}",
                        dry_run,
                    )
            return super().before_import_row(row, **kwargs)

    resource = Resource(import_job=import_job)

    skip_diff = resource._meta.skip_diff or resource._meta.skip_html_diff

    result = resource.import_data(dataset, dry_run=dry_run)
    change_job_status(import_job, "import", "4/5 Generating import summary", dry_run)

    if result.base_errors or result.row_errors():
        import_job.errors = "ERRORS zie change_summary"

    # save import summary
    context = {"result": result, "skip_diff": skip_diff}
    content = render_to_string("import_export_job/change_summary.html", context)
    import_job.change_summary.delete()
    import_job.change_summary.save(
        os.path.split(import_job.file.name)[1] + ".html",
        ContentFile(content.encode("utf-8")),
    )
    if not dry_run and (import_job.errors==""):
        import_job.imported = timezone.now()
    change_job_status(import_job, "import", "5/5 Import job finished", dry_run)
    import_job.save()


def run_import_job(pk, dry_run=True):
    logger.info(f"Importing {pk} dry-run {dry_run}")
    import_job = models.ImportJob.objects.get(pk=pk)
    try:
        _run_import_job(import_job, dry_run)
    except Exception as e:
        import_job.errors += _("Import error %s") % e + "\n"
        change_job_status(import_job, "import", "Import error", dry_run)
        import_job.save()
        return
