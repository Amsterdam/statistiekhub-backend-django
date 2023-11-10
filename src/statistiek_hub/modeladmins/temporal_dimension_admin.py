from django.contrib import admin

from statistiek_hub.resources.temporal_dimension_resource import TemporalDimensionResource

from .import_export_formats_mixin import ImportExportFormatsMixin


class TemporalDimensionAdmin(ImportExportFormatsMixin, admin.ModelAdmin):
    readonly_fields = ("enddate",)

    list_display = ("name", "id")
    list_filter = ("type",)
    ordering = ("id",)
    resource_class = TemporalDimensionResource

