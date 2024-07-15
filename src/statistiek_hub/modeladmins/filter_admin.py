from django.contrib import admin
from import_export.admin import ImportMixin

from statistiek_hub.resources.filter_resource import FilterResource

from .import_export_formats_mixin import ImportExportFormatsMixin


class FilterAdmin(ImportExportFormatsMixin, ImportMixin, admin.ModelAdmin):
    list_display = (
        "measure",
        "rule",
        "value_new",
    )
    ordering = ("measure",)
    raw_id_fields = ("measure",)
    resource_classes = [FilterResource]
