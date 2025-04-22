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
