from django.contrib import admin
from import_export.tmp_storages import MediaStorage

from statistiek_hub.models.observation import ObservationCalculated
from statistiek_hub.resources.observation_resource import ObservationResource

from .admin_mixins import CheckPermissionUserMixin, ImportExportFormatsMixin


class ObservationAdmin(ImportExportFormatsMixin, CheckPermissionUserMixin, admin.ModelAdmin):
    tmp_storage_class = MediaStorage
    list_display = (
        "id",
        "measure",
        "value",
        "temporaldimension",
        "spatialdimension",
        "created_at",
        "updated_at",
    )

    list_filter = ( ("measure__theme", admin.RelatedOnlyFieldListFilter),
        ("temporaldimension__type", admin.RelatedOnlyFieldListFilter),
        ("spatialdimension__type", admin.RelatedOnlyFieldListFilter),
    )
    search_help_text = "search on measure name"
    search_fields = ["measure__name"]

    raw_id_fields = ("measure", "temporaldimension", "spatialdimension")
    resource_classes = [ObservationResource]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return  ["measure", "temporaldimension", "spatialdimension"]
        else:  # Add obj
            return []
    


@admin.register(ObservationCalculated)
class ObservationCalculatedAdmin(admin.ModelAdmin):
    tmp_storage_class = MediaStorage
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
    ordering = ("measure",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False