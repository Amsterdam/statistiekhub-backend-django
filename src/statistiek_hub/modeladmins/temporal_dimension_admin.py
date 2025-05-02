from django.contrib import admin
from import_export.tmp_storages import MediaStorage

from statistiek_hub.resources.temporal_dimension_resource import (
    TemporalDimensionResource,
)

from .import_export_formats_mixin import ImportExportFormatsMixin


class TemporalDimensionAdmin(ImportExportFormatsMixin, admin.ModelAdmin):
    tmp_storage_class = MediaStorage
    readonly_fields = ("enddate", "year")

    list_display = (
        "id",
        "name",
        "year",
    )
    list_filter = ("type", "year")
    ordering = ("-year",)
    resource_classes = [TemporalDimensionResource]
