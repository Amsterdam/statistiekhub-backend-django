from django.contrib import admin
from import_export.tmp_storages import CacheStorage

from statistiek_hub.models.filter import Filter
from statistiek_hub.resources.measure_resource import MeasureResource

from .import_export_formats_mixin import ImportExportFormatsMixin


class FilterInline(admin.TabularInline):
    model = Filter
    fk_name = "measure"
    extra = 0  # <=== For remove empty fields from admin view


class MeasureAdmin(ImportExportFormatsMixin, admin.ModelAdmin):
    tmp_storage_class = CacheStorage     
    list_display = (
        "name",
        "label",
        "theme",
        "sensitive",
        "deprecated",
    )
    list_filter = (
        "theme",
        "unit",
        "sensitive",
        "deprecated",
        "created_at",
        "updated_at",
    )
    resource_classes = [MeasureResource]

    search_help_text = "search on measure name"
    search_fields = ["name"]

    fieldsets = (
        (
            None,
            {
                "fields": ("theme",),
            },
        ),
        (
            "Compulsory",
            {
                "fields": (
                    "name",
                    "label",
                    "definition",
                    "unit",
                    "decimals",
                    "source",
                ),
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "label_uk",
                    "definition_uk",
                    "description",
                    "parent",
                    "dimension",
                    "sensitive",
                ),
            },
        ),
        (
            "Product-specific",
            {
                "fields": ("calculation", "extra_attr"),
            },
        ),
        (
            "Vervallen",
            {
                "fields": ("deprecated", "deprecated_date", "deprecated_reason"),
            },
        ),
    )

    inlines = [FilterInline]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        return self.readonly_fields

    def _get_user_groups(self, request):
        # Collect user groups once
        if not hasattr(request, '_cached_user_groups'):
            request._cached_user_groups = request.user.groups.all()
        return request._cached_user_groups

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return obj.theme.group in self._get_user_groups(request)
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return obj.theme.group in self._get_user_groups(request)
        return super().has_delete_permission(request, obj)