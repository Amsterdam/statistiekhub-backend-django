from django.contrib import admin
from import_export.tmp_storages import MediaStorage
from leaflet.admin import LeafletGeoAdminMixin

from statistiek_hub.modeladmins.admin_mixins import (
    DynamicListFilter,
    ImportExportFormatsMixin,
)
from statistiek_hub.resources.spatial_dimension_resource import SpatialDimensionResource


class SourceDateFilter(DynamicListFilter):
    title = "source date"
    parameter_name = "source_date"
    filter_field = "source_date"


class SpatialDimensionAdmin(ImportExportFormatsMixin, LeafletGeoAdminMixin, admin.ModelAdmin):
    map_template = "leaflet/admin/custom_widget.html"

    tmp_storage_class = MediaStorage
    list_display = (
        "code",
        "name",
        "source_date",
        "type",
        "id",
    )
    list_filter = (("type", admin.RelatedOnlyFieldListFilter), SourceDateFilter)
    ordering = ("id",)
    search_help_text = "search on dimension name"
    search_fields = ["name", "id"]

    modifiable = False  # Make the leaflet map read-only
    resource_classes = [SpatialDimensionResource]
