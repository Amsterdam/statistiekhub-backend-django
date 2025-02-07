from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImportExportJobConfig(AppConfig):
    name = "import_export_job"
    verbose_name = _("Import Data")
