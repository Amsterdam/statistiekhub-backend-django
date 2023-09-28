import html2text
from django.conf import settings
from import_export.formats import base_formats
from statistiek_hub.utils.formatters import SCSV, GEOJSON

DEFAULT_FORMATS = [SCSV, base_formats.XLSX, base_formats.CSV, GEOJSON]

