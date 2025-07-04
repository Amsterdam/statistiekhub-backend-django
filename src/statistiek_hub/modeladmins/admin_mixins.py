from django.contrib import admin
from import_export.admin import ExportActionMixin, ImportMixin
from import_export.formats import base_formats

from statistiek_hub.utils.formatters import GEOJSON, SCSV


class ImportExportFormatsMixin(ImportMixin, ExportActionMixin):
    """overwrites the standard get_import_formats and get_export_formats from the ImportExportMixin"""

    def get_import_formats(self):
        """Returns available import formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV, GEOJSON]
        return formats

    def get_export_formats(self):
        """Returns available export formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV, base_formats.JSON]
        return formats
    

class CheckPermissionUserMixin:
    """checks user_group for change and delete permission on the obj,  used with admin.ModelAdmin as parent"""

    def _get_user_groups(self, request):
        # Collect user groups once
        if not hasattr(request, '_cached_user_groups'):
            request._cached_user_groups = request.user.groups.all()
        return request._cached_user_groups

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            theme_group = obj.measure.theme.group if hasattr(obj, 'measure') else obj.theme.group
            return theme_group in self._get_user_groups(request)
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            theme_group = obj.measure.theme.group if hasattr(obj, 'measure') else obj.theme.group
            return theme_group in self._get_user_groups(request)
        return super().has_delete_permission(request)
    

class GenericDateFilter(admin.SimpleListFilter):
    title = "date filter"
    parameter_name = "date_field"

    # The field to filter on, defaulting to "source_date"
    filter_field = "source_date"

    def lookups(self, request, model_admin):
        """
        Choices to propose all distinct values of the filter_field in the related model.
        """
        dates = list(
            model_admin.model.objects.order_by(self.filter_field)
            .values_list(self.filter_field, flat=True)
            .distinct()
        )
        # Create a list of tuples for the filter dropdown
        return [(str(date), str(date)) for date in dates]

    def queryset(self, request, queryset):
        """
        Filter the queryset based on the selected value.
        """
        if self.value():  # If a value is selected, filter the queryset
            filter_kwargs = {self.filter_field: self.value()}
            return queryset.filter(**filter_kwargs)
        return queryset        