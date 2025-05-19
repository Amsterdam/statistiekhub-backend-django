from django.contrib.admin import ModelAdmin
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