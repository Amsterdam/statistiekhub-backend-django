from . import tasks


def run_import_job_action(modeladmin, request, queryset):
    for instance in queryset:
        if instance.errors != '':
            message ="Errors not empty: perform dry-run first"
            tasks.change_job_status(instance, "import", f"{message}", dry_run=False)
            return
        tasks.logger.info("Importing %s dry-run: False" % (instance.pk))
        tasks.run_import_job(instance.pk, dry_run=False)

run_import_job_action.short_description = "Perform import"


def run_import_job_action_dry(modeladmin, request, queryset):
    for instance in queryset:
        tasks.logger.info("Importing %s dry-run: True" % (instance.pk))
        tasks.run_import_job(instance.pk, dry_run=True)

run_import_job_action_dry.short_description = "Perform dry-run"