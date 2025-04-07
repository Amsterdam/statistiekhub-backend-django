from import_export.admin import ExportActionMixin
from import_export.formats import base_formats

from statistiek_hub.utils.formatters import GEOJSON, SCSV


class ImportExportFormatsMixin(ExportActionMixin):
    """overwrites the standard get_import_formats and get_export_formats from the ImportExportMixin"""
    # TODO show_change_form_export= False is not working but should see: https://django-import-export.readthedocs.io/en/4.3.7/api_admin.html
    show_change_form_export= False #remove export button 

    def get_import_formats(self):
        """Returns available import formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV, GEOJSON, base_formats.JSON]
        return formats

    def get_export_formats(self):
        """Returns available export formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV, base_formats.JSON]
        return formats
