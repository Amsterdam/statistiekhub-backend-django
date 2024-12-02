import pandas as pd
from django.core.exceptions import ValidationError
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from referentie_tabellen.models import SpatialDimensionType, TemporalDimensionType
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension
from statistiek_hub.utils.check_functions import (
    check_exists_in_model,
    check_missing_fields,
)
from statistiek_hub.utils.converter import convert_str
from statistiek_hub.utils.datetime import add_timedelta, convert_to_date
from statistiek_hub.validations import get_instance



def set_stringfields_to_upper(df: pd.DataFrame) -> pd.DataFrame:
    df = df.map(lambda x: x.upper() if isinstance(x, str) else x)
    return df


class ObservationResource(ModelResource):

    def before_import(self, dataset, **kwargs):
        # check major error's first on Dataset (instead of row by row)

        errors = {}

        # check column_names importfile
        expected = [
            "measure",
            "spatial_code",
            "spatial_type",
            "spatial_date",
            "temporal_type",
            "temporal_date",
            "value",
        ]

        error = check_missing_fields(fields=dataset.headers, expected=expected)
        if error:
            errors["column_names"] = error

        else:
            # load querysets into pandas df
            dfmeasure = set_stringfields_to_upper(
                pd.DataFrame(list(Measure.objects.values("id", "name")))
            )

            dfspatialdim = set_stringfields_to_upper(
                pd.DataFrame(
                list(
                    SpatialDimension.objects.select_related("type").values(
                        "id", "code", "source_date", "type__name"
                    )
                )
            ))

            dftemporaldim = set_stringfields_to_upper(
                pd.DataFrame(
                list(
                    TemporalDimension.objects.select_related("type").values(
                        "id", "startdate", "type__name"
                    )
                )
            ))

            # load dataset to pandas dataframe
            df_main = dataset.df
            df_main = set_stringfields_to_upper(df_main)

            # convert 'date' to datetime.date format 
            df_main["spatial_date"] = df_main["spatial_date"].apply(convert_to_date)
            df_main["temporal_date"] = df_main["temporal_date"].apply(convert_to_date)

            check = {
                "measure_names": {
                    "dataset": df_main,
                    "dfmodel": dfmeasure,
                    "column": ["measure"],
                    "field": ["name"],
                },
                "spatial_types": {
                    "dataset": df_main,
                    "dfmodel": dfspatialdim,
                    "column": ["spatial_type"],
                    "field": ["type__name"],
                },
                "temporal_types": {
                    "dataset": df_main,
                    "dfmodel": dftemporaldim,
                    "column": ["temporal_type"],
                    "field": ["type__name"],
                },
                "spatial_codes": {
                    "dataset": df_main,
                    "dfmodel": dfspatialdim,
                    "column": ["spatial_code"],
                    "field": ["code"],
                },
                "spatial_dates": {
                    "dataset": df_main,
                    "dfmodel": dfspatialdim,
                    "column": ["spatial_date"],
                    "field": ["source_date"],
                },
                "spatial_dim": {
                    "dataset": df_main,
                    "dfmodel": dfspatialdim,
                    "column": ["spatial_date", "spatial_code", "spatial_type"],
                    "field": ["source_date", "code", "type__name"],
                },
                "temporal_dim": {
                    "dataset": df_main,
                    "dfmodel": dftemporaldim,
                    "column": ["temporal_date", "temporal_type"],
                    "field": ["startdate", "type__name"],
                },
            }

            # check measure_names exists
            for key in check:
                if check[key]["dfmodel"].empty:
                    errors[key] = ValueError(f"Model voor {key} is leeg")
                else:
                    error = check_exists_in_model(**check[key])
                    if error:
                        errors[key] = error

        if errors:
            # to speed validation -> if errors empty dataset so no row's will be checked
            del dataset[0 : len(dataset)]
            raise ValidationError(errors)
        
        # no errors
        # merge id spatialdim 
        merged_df = df_main.merge(dfspatialdim,  left_on=['spatial_code', 'spatial_type', 'spatial_date'],
                      right_on=['code', 'type__name', 'source_date'], how='left')
        merged_df = merged_df.rename(columns={'id': "spatialdimension"})

        # merge id temporaldim
        merged_df = merged_df.merge(dftemporaldim,  left_on= ["temporal_date", "temporal_type"],
                      right_on=["startdate", "type__name"], how='left')
        merged_df = merged_df.rename(columns={'id': "temporaldimension"})

        # merge id measure
        merged_df = merged_df.merge(dfmeasure,  left_on= ["measure"],
                      right_on=["name"], how='left')
        merged_df = merged_df.rename(columns={'id': "measure", "measure": "name"})

        # clean df
        df_main = merged_df[["measure", "spatialdimension", "temporaldimension", "value"]]
        df_main.loc[:, 'value'] = df_main['value'].apply(convert_str)
        print(df_main.head())

        # Converteer de DataFrame naar een Tablib dataset
        dataset.df = df_main
        print(dataset[0:5])
        

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with empty value,
        necessary since importfile for Observationmodel allows blank value"""

        if row["value"] in [""]:
            return True
        else:
            return super().skip_row(instance, original, row, import_validation_errors)


    class Meta:
        model = Observation
        use_bulk = True
        skip_unchanged = True
        report_skipped = True
        exclude = ("id", "created_at", "updated_at")
        import_id_fields = ("measure", "spatialdimension", "temporaldimension")
