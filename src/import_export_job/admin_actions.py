from . import tasks


def run_import_job_action(modeladmin, request, queryset):
    for instance in queryset:
        tasks.logger.info("Importing %s dry-run: False" % (instance.pk))
        tasks.run_import_job(instance.pk, dry_run=False)


run_import_job_action.short_description = "Perform import"