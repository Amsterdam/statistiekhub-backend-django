# Author: Timothy Hobbs <timothy <at> hobbs.cz>
import logging
import os
from io import StringIO

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from pandas import DataFrame

from statistiek_hub.csv_import.observation.result import Result

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


def _update_status(step, message, import_job, dry_run):
    change_job_status(import_job, "import", f"{step} {message}", dry_run)


def _run_import_job(import_job, dry_run=True):
    _update_status("1/4", "Import started", import_job, dry_run)
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

    _update_status("2/4", "Processing import data", import_job, dry_run)
    resource = model_config.resource()

    skip_diff = resource._meta.skip_diff or resource._meta.skip_html_diff

    result = resource.import_data(
        dataset,
        dry_run=dry_run,
    )
    _update_status("3/4", "Generating import summary", import_job, dry_run)

    if result.has_errors() or result.has_validation_errors():
        import_job.errors = "ERRORS zie change_summary"

    # save import summary
    context = {"result": result, "skip_diff": skip_diff}
    content = render_to_string("import_export_job/change_summary.html", context)
    import_job.change_summary.delete()
    import_job.change_summary.save(
        os.path.split(import_job.file.name)[1] + ".html",
        ContentFile(content.encode("utf-8")),
    )

    if not dry_run and (import_job.errors == ""):
        import_job.imported = timezone.now()

    _update_status("4/4", "Import job finished", import_job, dry_run)
    import_job.save()


def _run_observation_import_job(import_job, dry_run=True):
    """
    Run the custom Observation import job
    """
    _update_status("1/4", "Import started (Custom Observation import)", import_job, dry_run)

    # Clear the import errors
    import_job.errors = ""

    try:
        data = import_job.file.read()
        if isinstance(data, bytes):
            data = data.decode("utf8")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError("Imported file has a wrong encoding" + str(e)) from e
    except Exception as e:
        raise Exception("Error reading file" + str(e)) from e

    _update_status("2/4", "Processing import data (Custom Observation import)", import_job, dry_run)

    from statistiek_hub.csv_import.observation import import_csv

    errors = []
    try:
        result = import_csv(filepath_or_buffer=StringIO(data), dry_run=dry_run)
    except Exception as e:
        if hasattr(e, "error_list"):  # Django ValidationError with multiple errors
            errors = []
            for error in e.error_list:
                if isinstance(error, Exception) and hasattr(error, "messages"):
                    errors.extend(error.messages)
                elif isinstance(error, Exception) and hasattr(error, "message"):
                    errors.append(error.message)
                else:
                    errors.append(str(error))
        elif hasattr(e, "messages"):  # Some exceptions have a messages attribute (list)
            errors = e.messages if isinstance(e.messages, list) else [e.messages]
        elif isinstance(e, list):  # e is already a list
            errors = e
        else:  # Single error - wrap in list
            errors = [str(e)]

        import_job.errors = "ERRORS zie change_summary"
        result = Result(DataFrame())

    _update_status(
        "3/4",
        "Generating import summary (Custom Observation import)",
        import_job,
        dry_run,
    )

    columns_to_html = [
        "id",
        "value",
        "measure_id",
        "spatialdimension_id",
        "temporaldimension_id",
    ]
    inserted_html = ""
    if result.total_inserted:
        inserted_html = result.inserted[columns_to_html].to_html(index=False, border=1)
    updated_html = ""
    if result.total_updated:
        updated_html = result.updated[columns_to_html].to_html(index=False, border=1)
    deleted_html = ""
    if result.total_deleted:
        deleted_html = result.deleted[
            [
                "id",
                "original_value",
                "value",
                "measure_id",
                "spatialdimension_id",
                "temporaldimension_id",
            ]
        ].to_html(index=False, border=1)

    context = {
        "csv_name": import_job.file.name,
        "dry_run": "enabled" if dry_run else "disabled",
        "result": result,
        "inserted_html": inserted_html,
        "updated_html": updated_html,
        "deleted_html": deleted_html,
        "errors": errors,
    }
    content = render_to_string("csv_import/observation.html", context)

    import_job.change_summary.delete()
    import_job.change_summary.save(
        os.path.split(import_job.file.name)[1] + ".html",
        ContentFile(content.encode("utf-8")),
    )

    if not dry_run and (import_job.errors == ""):
        import_job.imported = timezone.now()

    _update_status("4/4", "Import job finished (Custom Observation import)", import_job, dry_run)
    import_job.save()


@shared_task
def run_import_job(pk: int, dry_run: bool = True):
    logger.info(f"Importing {pk} dry-run {dry_run}")
    import_job = models.ImportJob.objects.get(pk=pk)

    try:
        if import_job.model.lower() == "observation":
            logger.info("Run the custom observation import")
            _run_observation_import_job(import_job, dry_run)
        else:
            logger.info("Run the import_export job")
            _run_import_job(import_job, dry_run)
    except Exception as e:
        logger.info(f"error op _run_import_job {pk}: {e}")
        import_job.errors += _("Import error %s") % e + "\n"
        change_job_status(import_job, "import", "Import error", dry_run)
        import_job.save()
        return
