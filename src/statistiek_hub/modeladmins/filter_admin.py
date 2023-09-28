from django.contrib import admin
from import_export.admin import ImportMixin

from statistiek_hub.resources.filter_resource import FilterResource
from statistiek_hub.utils.formatters import SCSV
from . import_export_formats_mixin import ImportExportFormatsMixin

class FilterAdmin(ImportExportFormatsMixin, ImportMixin, admin.ModelAdmin):
    list_display = (
        "measure",
        "rule",
        "value_new",
        "id",
    )
    ordering = ("measure",)
    resource_classes = [FilterResource]
