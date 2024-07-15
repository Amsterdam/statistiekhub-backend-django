from django.contrib import admin
from import_export.tmp_storages import CacheStorage

from statistiek_hub.resources.temporal_dimension_resource import (
    TemporalDimensionResource,
)

from .import_export_formats_mixin import ImportExportFormatsMixin


class TemporalDimensionAdmin(ImportExportFormatsMixin, admin.ModelAdmin):
    tmp_storage_class = CacheStorage
    readonly_fields = ("enddate", "year")

    list_display = (
        "name",
        "year",
    )
    list_filter = ("type", "year")
    ordering = ("-year",)
    resource_class = TemporalDimensionResource
