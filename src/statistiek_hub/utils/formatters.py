import csv
import json

import pandas as pd
import tablib
from django.core.exceptions import ValidationError
from import_export.formats import base_formats
from statistiek_hub.utils.timer import timeit


class SCSV(base_formats.CSV):
    def get_title(self):
        return "semicolon_csv"

    @timeit
    def create_dataset(self, in_stream, **kwargs):
        delimiter = csv.Sniffer().sniff(in_stream, delimiters=";,").delimiter
        if delimiter != ";":
            raise ValidationError(
                f"CSV format is using `{delimiter}` delimiter,"
                + " but it should be `;` delimiter"
            )
        kwargs["delimiter"] = delimiter
        kwargs["format"] = "csv"
        return tablib.import_set(in_stream, **kwargs)


class GEOJSON(base_formats.TablibFormat):
    def get_title(self):
        return "geojson"

    def create_dataset(self, in_stream, **kwargs):
        """
        Create tablib.dataset from geojson.
        """

        data = json.load(tablib.utils.normalize_input(in_stream))

        try:
            crs = data["crs"]
        except:  # if not in Geojson -> default crs RD
            crs = {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:EPSG::28992"},
            }

        df = data["features"]
        tmp = pd.DataFrame.from_records(df)
        df_properties = pd.DataFrame.from_records(tmp["properties"])

        # adds crs to geometry field -> necessary for function GEOSGeometry in resource.py
        # function GEOSGeometry has a bug at this moment (6-3-2023) when reading geojson geometry-field;
        # it defaults always to srid=4326 while we need srid=28992.
        # solution: add crs of the geojson to the geometry-field.
        tmp_list = []
        for feature in df:
            geometry = feature["geometry"]
            geometry["crs"] = crs
            tmp_list.append(str(geometry))

        df_properties["geometry"] = tmp_list

        _dset = tablib.Dataset()
        _dset.dict = df_properties.to_dict(orient="records")

        return _dset
