from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from import_export.tmp_storages import MediaStorage

from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.resources.measure_resource import MeasureResource

from .admin_mixins import CheckPermissionUserMixin, ImportExportFormatsMixin


class MeasureForm(forms.ModelForm):
    class Meta:
        model = Measure
        fields = "__all__"

    def clean_team(self):
        team = self.cleaned_data.get("team")
        if team and not self.request.user.is_superuser:
            user_groups = self.request.user.groups.all()
            if team not in user_groups:
                raise ValidationError("You can only assign measures to groups of which you are a member.")
        return team


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
    resource_classes = [MeasureResource]
    form = MeasureForm

    def get_form(self, request, obj=None, **kwargs):
        # Pass the request object to form for validation
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    search_help_text = "search on measure name"
    search_fields = ["name", "id"]

    list_display = (
        "id",
        "name",
        "label",
        "team",
        "theme",
        "sensitive",
        "deprecated",
    )
    list_filter = (
        "team",
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

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "team",
                    "theme",
                ),
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
