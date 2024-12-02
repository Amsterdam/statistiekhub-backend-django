from django.contrib import admin
from import_export.tmp_storages import CacheStorage

from statistiek_hub.models.observation import ObservationCalculated
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

    def _get_user_groups(self, request):
        # Collect user groups once
        if not hasattr(request, '_cached_user_groups'):
            request._cached_user_groups = request.user.groups.all()
        return request._cached_user_groups

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return obj.measure.theme.group in self._get_user_groups(request)
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return obj.measure.theme.group in self._get_user_groups(request)
        return super().has_delete_permission(request, obj)    


@admin.register(ObservationCalculated)
class ObservationCalculatedAdmin(admin.ModelAdmin):
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
    ordering = ("measure",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False