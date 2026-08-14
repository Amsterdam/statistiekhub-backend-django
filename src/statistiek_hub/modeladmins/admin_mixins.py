from django.contrib import admin
from import_export.admin import ExportActionMixin, ImportMixin
from import_export.formats import base_formats

from statistiek_hub.utils.formatters import GEOJSON, SCSV


class ImportExportFormatsMixin(ImportMixin, ExportActionMixin):
    """overwrites the standard get_import_formats and get_export_formats from the ImportExportMixin"""

    def get_import_formats(self):
        """Returns available import formats."""
        formats = [SCSV, base_formats.CSV, GEOJSON]
        return formats

    def get_export_formats(self):
        """Returns available export formats."""
        formats = [SCSV, base_formats.CSV, base_formats.JSON]
        return formats


class CheckPermissionUserMixin:
    """checks user_group for change and delete permission on the obj,  used with admin.ModelAdmin as parent"""

    def _get_user_groups(self, request):
        """Cache user groups on the request to avoid duplicate DB queries per request."""
        # Collect user groups once
        if not hasattr(request, "_cached_user_groups"):
            request._cached_user_groups = request.user.groups.all()
        return request._cached_user_groups

    def _has_team_permission(self, request, obj):
        """Return True when the user belongs to the team that manage the object."""
        team = obj.measure.team if hasattr(obj, "measure") else obj.team
        in_group = team in self._get_user_groups(request)
        return in_group or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return self._has_team_permission(request, obj)
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return self._has_team_permission(request, obj)
        return super().has_delete_permission(request)


class DeprecatedMeasureRelationAdminMixin:
    """Block change/delete/add-linking for rows that point to deprecated measures."""

    measure_fk_name = "measure"

    def _obj_has_deprecated_measure(self, obj):
        """Check whether this row points to a deprecated measure."""
        if obj is None:
            return False
        measure = getattr(obj, self.measure_fk_name, None)
        return bool(measure and measure.deprecated)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Hide deprecated measures from FK selectors in admin forms."""
        if db_field.name == self.measure_fk_name:
            from statistiek_hub.models.measure import Measure

            kwargs["queryset"] = Measure.objects.filter(deprecated=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        allowed = super().has_change_permission(request, obj)
        if not allowed:
            return False
        if self._obj_has_deprecated_measure(obj):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        allowed = super().has_delete_permission(request, obj)
        if not allowed:
            return False
        if self._obj_has_deprecated_measure(obj):
            return False
        return True

    def delete_queryset(self, request, queryset):
        """Prevent bulk actions from deleting rows linked to deprecated measures."""
        super().delete_queryset(request, queryset.filter(measure__deprecated=False))


class DeprecatedParentMeasureInlineMixin:
    """Freeze inline add/edit/delete when the parent Measure is deprecated."""

    deprecated_parent_readonly_fields = ()

    def _is_deprecated_parent(self, obj):
        return bool(obj is not None and obj.deprecated)

    def has_add_permission(self, request, obj=None):
        if self._is_deprecated_parent(obj):
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_deprecated_parent(obj):
            return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if self._is_deprecated_parent(obj):
            return list(self.deprecated_parent_readonly_fields)
        return super().get_readonly_fields(request, obj)


class DynamicListFilter(admin.SimpleListFilter):
    title = "Dynamic Field"  # Display name in the admin sidebar
    parameter_name = "dynamic_field"  # Query parameter name

    filter_field = "source_date"

    def lookups(self, request, model_admin):
        # Get the current queryset
        queryset = model_admin.get_queryset(request)
        values = set(queryset.values_list(self.filter_field, flat=True).order_by(self.filter_field).distinct())

        # Return a list of tuples (value, display_name)
        return [(str(value), str(value)) for value in values]

    def queryset(self, request, queryset):
        """Filter the queryset based on the selected value."""
        if self.value():
            filter_kwargs = {self.filter_field: self.value()}
            return queryset.filter(**filter_kwargs)
        return queryset
