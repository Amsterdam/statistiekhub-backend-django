import csv
import json

import pandas as pd
import tablib
from django.core.exceptions import ValidationError
from import_export.formats import base_formats


class SCSV(base_formats.CSV):
    CONTENT_TYPE = "semicolon text/csv"

    def get_title(self):
        return "semicolon_csv"

    def create_dataset(self, in_stream, **kwargs):
        if isinstance(in_stream, bytes) and self.encoding:
            in_stream = in_stream.decode(self.encoding)

        delimiter = csv.Sniffer().sniff(in_stream, delimiters=";,").delimiter
        if delimiter != ";":
            raise ValidationError(
                f"CSV format is using `{delimiter}` delimiter,"
                + " but it should be `;` delimiter"
            )
        kwargs["delimiter"] = delimiter
        kwargs["format"] = "csv"
        return tablib.import_set(in_stream, **kwargs)

    def export_data(self, dataset, **kwargs):
        # remove the deprecated `escape_output` param if present
        kwargs.pop("escape_output", None)
        if kwargs.pop("escape_html", None):
            self._escape_html(dataset)
        if kwargs.pop("escape_formulae", None):
            self._escape_formulae(dataset)

        kwargs["delimiter"] = ";"
        return dataset.export("csv", **kwargs)


class GEOJSON(base_formats.TablibFormat):
    CONTENT_TYPE = "geojson"

    def get_title(self):
        return "geojson"

    def create_dataset(self, in_stream, **kwargs):
        """
        Create tablib.dataset from geojson.
        """
        print("------------------------------- in create dataset geojson")

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

        # json-field "geometry" is saved in tablib-field "geom"
        df_properties["geom"] = tmp_list

        _dset = tablib.Dataset()
        _dset.dict = df_properties.to_dict(orient="records")

        return _dset
