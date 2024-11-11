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
    def update_status(step, message):
        change_job_status(import_job, "import", f"{step} {message}", dry_run)

    update_status("1/4", "Import started")
    import_job.errors = ""

    model_config = ModelConfig(**importables[import_job.model])
    import_format = get_format(import_job)

    try:
        data = import_job.file.read()
        if isinstance(data, bytes):
            data = data.decode("utf8")
        dataset = import_format.create_dataset(data)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError("Imported file has a wrong encoding" + str(e)) from e
    except Exception as e:
        raise Exception("Error reading file" + str(e)) from e

    update_status("2/4", "Processing import data")
    resource = model_config.resource()
    
    skip_diff = resource._meta.skip_diff or resource._meta.skip_html_diff

    result = resource.import_data(dataset, dry_run=dry_run)
    update_status("3/4", "Generating import summary")

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

    update_status("4/4", "Import job finished")
    import_job.save()


def run_import_job(pk, dry_run=True):
    logger.info(f"Importing {pk} dry-run {dry_run}")
    import_job = models.ImportJob.objects.get(pk=pk)

    try:        
        _run_import_job(import_job, dry_run)
    except Exception as e:
        logger.info(f"error op _run_import_job {pk}: {e}")
        import_job.errors += _("Import error %s") % e + "\n"
        change_job_status(import_job, "import", "Import error", dry_run)
        import_job.save()
        return
