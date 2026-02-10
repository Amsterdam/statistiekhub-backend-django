from django.contrib import admin
from import_export.tmp_storages import MediaStorage

from statistiek_hub.models.filter import Filter
from statistiek_hub.resources.measure_resource import MeasureResource

from .admin_mixins import CheckPermissionUserMixin, ImportExportFormatsMixin


class CalculationFilter(admin.SimpleListFilter):
    title = "calculation"
    parameter_name = "calculation"

    def lookups(self, request, model_admin):
        return (
            ("true", "Yes"),
            ("false", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.exclude(calculation="")
        elif self.value() == "false":
            return queryset.filter(calculation="")
        return queryset


class FilterInline(admin.TabularInline):
    model = Filter
    fk_name = "measure"
    extra = 0  # <=== For remove empty fields from admin view


class MeasureAdmin(ImportExportFormatsMixin, CheckPermissionUserMixin, admin.ModelAdmin):
    tmp_storage_class = MediaStorage
    list_display = (
        "id",
        "name",
        "label",
        "theme",
        "sensitive",
        "deprecated",
    )
    list_filter = (
        "theme",
        "temporaltype",
        CalculationFilter,
        "sensitive",
        "deprecated",
        "unit",
        "created_at",
        "updated_at",
        "source",
    )
    resource_classes = [MeasureResource]

    search_help_text = "search on measure name"
    search_fields = ["name", "id"]

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
                    "temporaltype",
                    "sensitive",
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
        if obj:
            return ["name"]
        return []
