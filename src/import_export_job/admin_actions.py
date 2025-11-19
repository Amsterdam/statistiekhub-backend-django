import logging

from .job import change_job_status
from .tasks import import_job_celery_task

logger = logging.getLogger()


def run_import_job_action(modeladmin, request, queryset):
    for instance in queryset:
        if instance.errors != "":
            message = "Errors not empty: perform dry-run first"
            change_job_status(instance, "import", f"{message}", dry_run=False)
            return
        logger.info("Importing %s dry-run: False" % (instance.pk))
        import_job_celery_task.delay(pk=instance.pk, dry_run=False)


run_import_job_action.short_description = "Perform import"


def run_import_job_action_dry(modeladmin, request, queryset):
    for instance in queryset:
        logger.info("Importing %s dry-run: True" % (instance.pk))
        import_job_celery_task.delay(pk=instance.pk, dry_run=True)


run_import_job_action_dry.short_description = "Perform dry-run"
