from django.contrib import admin
from import_export.admin import ImportExportMixin

from statistiek_hub.models.filter import Filter
from statistiek_hub.resources.measure_resource import MeasureResource

from .import_export_formats_mixin import ImportExportFormatsMixin


class FilterInline(admin.TabularInline):
    model = Filter
    fk_name = "measure"
    extra = 0  # <=== For remove empty fields from admin view


class MeasureAdmin(ImportExportFormatsMixin, ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "theme",
        "deprecated",
        "owner",
    )
    list_filter = ("theme", "unit", "deprecated", "created_at", "updated_at")
    resource_classes = [MeasureResource]
    readonly_fields = [
        "owner",
    ]
    search_help_text = "search on measure name"
    search_fields = ["name"]

    fieldsets = (
        (
            None,
            {
                "fields": ("owner",),
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
                    "theme",
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

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        return self.readonly_fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    # measure field 'owner' get's filled automaticaly
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Only set owner during the first save.
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    inlines = [FilterInline]
