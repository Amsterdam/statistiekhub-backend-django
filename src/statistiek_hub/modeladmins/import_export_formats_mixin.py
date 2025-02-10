from import_export.admin import ExportActionModelAdmin, ImportExportMixin
from import_export.formats import base_formats

from statistiek_hub.utils.formatters import GEOJSON, SCSV


class ImportExportFormatsMixin(ImportExportMixin, ExportActionModelAdmin):
    """overwrites the standard get_import_formats and get_export_formats from the ImoprtExportMixin"""

    def get_import_formats(self):
        """Returns available import formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV, GEOJSON]
        return formats

    def get_export_formats(self):
        """Returns available export formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV]
        return formats
