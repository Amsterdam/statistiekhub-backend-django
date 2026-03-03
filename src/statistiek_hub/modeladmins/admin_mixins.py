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
        # Collect user groups once
        if not hasattr(request, "_cached_user_groups"):
            request._cached_user_groups = request.user.groups.all()
        return request._cached_user_groups

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            team = obj.measure.team if hasattr(obj, "measure") else obj.team
            in_group = team in self._get_user_groups(request)
            return in_group or request.user.is_superuser
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            team = obj.measure.team if hasattr(obj, "measure") else obj.team
            in_group = team in self._get_user_groups(request)
            return in_group or request.user.is_superuser
        return super().has_delete_permission(request)


class DynamicListFilter(admin.SimpleListFilter):
    title = "Dynamic Field"  # Display name in the admin sidebar
    parameter_name = "dynamic_field"  # Query parameter name

    filter_field = "source_date"

    def lookups(self, request, model_admin):
        # Get the current queryset
        queryset = model_admin.get_queryset(request)
        values = set(queryset.values_list(self.filter_field, flat=True).distinct())

        # Return a list of tuples (value, display_name)
        return [(str(value), str(value)) for value in values]

    def queryset(self, request, queryset):
        """Filter the queryset based on the selected value."""
        if self.value():
            filter_kwargs = {self.filter_field: self.value()}
            return queryset.filter(**filter_kwargs)
        return queryset
