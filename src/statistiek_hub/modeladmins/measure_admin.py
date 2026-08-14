from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from import_export.tmp_storages import MediaStorage

from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.resources.measure_resource import MeasureResource

from .admin_mixins import (
    CheckPermissionUserMixin,
    DeprecatedParentMeasureInlineMixin,
    ImportExportFormatsMixin,
)


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

    def clean_themes_items(self):
        themes = self.cleaned_data.get("themes")
        if not themes:
            raise ValidationError("Selecteer minimaal één thema.")
        return themes

    def clean_sources_items(self):
        sources = self.cleaned_data.get("sources")
        if not sources:
            raise ValidationError("Selecteer minimaal één bron.")
        return sources


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


class FilterInline(DeprecatedParentMeasureInlineMixin, admin.TabularInline):
    model = Filter
    fk_name = "measure"
    extra = 0  # <=== For remove empty fields from admin view
    deprecated_parent_readonly_fields = ("measure", "rule", "value_new")


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
    autocomplete_fields = [
        "themes",
        "sources",
    ]

    list_display = (
        "id",
        "name",
        "label",
        "team",
        "sensitive",
        "deprecated",
    )
    list_filter = (
        "team",
        "themes",
        "temporaltype",
        CalculationFilter,
        "sensitive",
        "deprecated",
        "unit",
        "created_at",
        "updated_at",
        "sources",
    )

    fieldsets = (
        (
            None,
            {
                "fields": ("team",),
            },
        ),
        (
            "Verplichte velden",
            {
                "fields": (
                    "name",
                    "label",
                    "themes",
                    "definition",
                    "unit",
                    "decimals",
                    "sources",
                    "temporaltype",
                    "sensitive",
                ),
            },
        ),
        (
            "Optionele velden",
            {
                "fields": (
                    "label_short",
                    "description",
                    "frequency",
                    "calculation",
                ),
            },
        ),
        (
            "Engelstalige velden",
            {
                "fields": (
                    "label_uk",
                    "label_short_uk",
                    "definition_uk",
                    "description_uk",
                    "frequency_uk",
                ),
            },
        ),
        (
            "Product-specific",
            {
                "fields": ("extra_attr",),
            },
        ),
        (
            "Status velden",
            {
                "fields": ("deprecated", "deprecated_date", "deprecated_reason"),
            },
        ),
    )

    inlines = [FilterInline]

    deprecated_only_editable_fields = (
        "deprecated",
        "deprecated_date",
        "deprecated_reason",
    )

    def _get_deprecated_readonly_fields(self):
        all_fields = []
        for _, config in self.fieldsets:
            all_fields.extend(config.get("fields", ()))

        editable = set(self.deprecated_only_editable_fields)
        readonly_fields = [field for field in all_fields if field not in editable]

        # Keep order stable and remove duplicates.
        return list(dict.fromkeys(readonly_fields))

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.deprecated:
            return self._get_deprecated_readonly_fields()
        if obj:
            return ["name"]
        return []

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        return not (obj is not None and obj.deprecated)

    def delete_queryset(self, request, queryset):
        # Prevent bulk delete from removing deprecated measures.
        super().delete_queryset(request, queryset.filter(deprecated=False))
