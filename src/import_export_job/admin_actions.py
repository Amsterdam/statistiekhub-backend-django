from django.utils.translation import gettext_lazy as _

from job_consumer.job_tools import store_job_in_queue

from . import tasks


def run_import_job_action(modeladmin, request, queryset):
    for instance in queryset:
        tasks.logger.info("Importing %s dry-run: False" % (instance.pk))
        store_job_in_queue(instance.pk, dry_run=False)

run_import_job_action.short_description = _("Perform import")


def run_import_job_action_dry(modeladmin, request, queryset):
    for instance in queryset:
        tasks.logger.info("Importing %s dry-run: True" % (instance.pk))
        store_job_in_queue(instance.pk, dry_run=True)

run_import_job_action_dry.short_description = _("Perform dry import")
