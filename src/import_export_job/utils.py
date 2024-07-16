from import_export.formats import base_formats

from statistiek_hub.utils.formatters import GEOJSON, SCSV

DEFAULT_FORMATS = [SCSV, base_formats.XLSX, base_formats.CSV, GEOJSON]
