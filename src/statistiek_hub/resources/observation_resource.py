import pandas as pd
from django.core.exceptions import ValidationError
from import_export.resources import ModelResource

from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension
from statistiek_hub.utils.check_functions import (
    check_exists_in_model,
    check_missing_fields,
    check_temporaldimensiontype_observation_vs_measure,
)
from statistiek_hub.utils.converter import convert_str, set_stringfields_to_upper
from statistiek_hub.utils.datetime import convert_to_date


class ObservationResource(ModelResource):
    delete_instance_empty_row_value = set()

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
                pd.DataFrame(list(Measure.objects.values("id", "name", "temporaltype", "deprecated")))
            )

            dfspatialdim = set_stringfields_to_upper(
                pd.DataFrame(
                    list(
                        SpatialDimension.objects.select_related("type").values(
                            "id", "code", "source_date", "type__name"
                        )
                    )
                )
            )

            dftemporaldim = set_stringfields_to_upper(
                pd.DataFrame(
                    list(
                        TemporalDimension.objects.select_related("type").values(
                            "id", "startdate", "type__name", "type__type"
                        )
                    )
                )
            )

            # load dataset to pandas dataframe
            df_main = dataset.df
            df_main = set_stringfields_to_upper(df_main)

            # convert 'date' to datetime.date format
            df_main["spatial_date"] = df_main["spatial_date"].apply(convert_to_date)
            df_main["temporal_date"] = df_main["temporal_date"].apply(convert_to_date)

            # check measure names: must exist and may not be deprecated
            if dfmeasure.empty:
                errors["measure_names"] = ValueError("Model voor measure_names is leeg")
            else:
                imported_measure_names = set(df_main["measure"].astype(str).str.upper())
                known_measure_names = set(dfmeasure["name"].astype(str).str.upper())
                deprecated_measure_names = set(dfmeasure.loc[dfmeasure["deprecated"], "name"].astype(str).str.upper())

                unknown_in_dataset = sorted(imported_measure_names - known_measure_names)
                if unknown_in_dataset:
                    errors["measure_names"] = f"De volgende variabelen in measure bestaan niet: {unknown_in_dataset}"

                deprecated_in_dataset = sorted(imported_measure_names & deprecated_measure_names)
                if deprecated_in_dataset:
                    errors["measure_deprecated"] = (
                        f"Vervallen variabelen mogen niet geimporteerd worden: {deprecated_in_dataset}"
                    )

            check = {
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

            # check spatial and temporal dimensions exist
            for key in check:
                if check[key]["dfmodel"].empty:
                    errors[key] = ValueError(f"Model voor {key} is leeg")
                else:
                    error = check_exists_in_model(**check[key])
                    if error:
                        errors[key] = error

            # check temporaldimensiontype of observation with measure
            if error := check_temporaldimensiontype_observation_vs_measure(
                df_main=df_main,
                dftemporaldim=dftemporaldim,
                dfmeasure=dfmeasure,
            ):
                errors["temporaltype"] = error

        if errors:
            # to speed validation -> if errors empty dataset so no row's will be checked
            del dataset[0 : len(dataset)]
            raise ValidationError(errors)

        # no errors
        # merge id spatialdim
        merged_df = df_main.merge(
            dfspatialdim,
            left_on=["spatial_code", "spatial_type", "spatial_date"],
            right_on=["code", "type__name", "source_date"],
            how="left",
        )
        merged_df = merged_df.rename(columns={"id": "spatialdimension"})

        # merge id temporaldim
        merged_df = merged_df.merge(
            dftemporaldim,
            left_on=["temporal_date", "temporal_type"],
            right_on=["startdate", "type__name"],
            how="left",
        )
        merged_df = merged_df.rename(columns={"id": "temporaldimension"})

        # merge id measure
        merged_df = merged_df.merge(dfmeasure, left_on=["measure"], right_on=["name"], how="left")
        merged_df = merged_df.rename(columns={"id": "measure", "measure": "name"})

        # clean df
        df_main = merged_df[["measure", "spatialdimension", "temporaldimension", "value"]]
        df_main.loc[:, "value"] = df_main["value"].apply(convert_str)

        # Converteer de DataFrame terug naar een Tablib dataset
        dataset.df = df_main

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with empty value, after deleting database-obj if not empty
        necessary so empty value import overwrites database-obj otherwise database-obj keeps wrong value
        """

        if row["value"] in [""]:
            self.delete_instance_empty_row_value.add(original.id)
            return True
        else:
            return super().skip_row(instance, original, row, import_validation_errors)

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        Observation.objects.filter(id__in=self.delete_instance_empty_row_value).delete()
        self.delete_instance_empty_row_value = set()

    class Meta:
        model = Observation
        skip_unchanged = True
        exclude = ("id", "created_at", "updated_at")
        import_id_fields = ("measure", "spatialdimension", "temporaldimension")
