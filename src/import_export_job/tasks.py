import logging

from import_export_job.job import run_import_job
from import_export_job.models import ImportJob
from main.celery import app

logger = logging.getLogger(__name__)


@app.task(
    soft_time_limit=60 * 30,
    time_limit=60 * 35,
)
def import_job_celery_task(pk: int, dry_run: bool = True) -> None:
    logger.info(f"ImportJob #{pk} started")

    import_job = None

    try:
        import_job = ImportJob.objects.get(pk=pk)
    except ImportJob.DoesNotExist:
        logger.error(f"ImportJob #{pk} not found")

    if import_job:
        try:
            run_import_job(import_job.pk, dry_run)
        except Exception as e:
            logger.exception(f"ImportJob #{pk} exceptions: {e}")

    logger.info(f"ImportJob #{pk} completed!")
    return
