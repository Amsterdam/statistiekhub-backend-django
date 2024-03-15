from django.contrib import admin
from import_export.tmp_storages import CacheStorage

from statistiek_hub.resources.observation_resource import ObservationResource

from .import_export_formats_mixin import ImportExportFormatsMixin


class ObservationAdmin(ImportExportFormatsMixin, admin.ModelAdmin):
    tmp_storage_class = CacheStorage
    list_display = (
        "id",
        "measure",
        "value",
        "temporaldimension",
        "spatialdimension",
        "created_at",
        "updated_at",
    )

    list_filter = (
        ("temporaldimension__type", admin.RelatedOnlyFieldListFilter),
        ("spatialdimension__type", admin.RelatedOnlyFieldListFilter),
    )
    search_help_text = "search on measure name"
    search_fields = ["measure__name"]

    resource_classes = [ObservationResource]
