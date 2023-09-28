from import_export.formats import base_formats
from statistiek_hub.utils.formatters import SCSV

class ImportExportFormatsMixin():
    """ overwrites the standard get_import_formats and get_export_formats from the ImoprtExportMixin
        because it's an overwrite it must go to the left of the 'ImportExportMixin' class
    """

    def get_import_formats(self):
        """Returns available import formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV]
        return formats

    def get_export_formats(self):
        """Returns available import formats."""
        formats = [SCSV, base_formats.XLSX, base_formats.CSV]
        return formats
