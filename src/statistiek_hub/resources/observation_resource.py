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
    SimpleError,
    check_exists_in_model,
    check_missing_fields,
)
from statistiek_hub.utils.converter import convert_str
from statistiek_hub.utils.datetime import add_timedelta, convert_to_date
from statistiek_hub.validations import get_instance

CHUNKSIZE = 5000


class MeasureForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        measure, _ = get_instance(
            model=Measure, field="name", row=row, column="measure"
        )

        return measure


class SpatialForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        spatial_code = row["spatial_code"]
        spatial_type, _ = get_instance(
            model=SpatialDimensionType, field="name", row=row, column="spatial_type"
        )

        try:
            spatial_date = convert_to_date(row["spatial_date"])
        except ValueError:
            spatial_date = None
        spatial_date = (
            SpatialDimension.objects.filter(
                code__iexact=spatial_code, type=spatial_type
            )
            .order_by("source_date")
            .latest("source_date")
        ).source_date

        spatial = SpatialDimension.objects.get(
            code__iexact=spatial_code, type=spatial_type, source_date=spatial_date
        )
        return spatial


class TemporalForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        temporal_type, _ = get_instance(
            model=TemporalDimensionType, field="name", row=row, column="temporal_type"
        )
        start_date = convert_to_date(row["temporal_date"])
        end_date = add_timedelta(start_date, temporal_type)

        temporal, created = TemporalDimension.objects.get_or_create(
            type=temporal_type,
            startdate=start_date,
            enddate=end_date,
            defaults={
                "name": f"{temporal_type}: {start_date.strftime('%Y-%m-%d')}-->{end_date.strftime('%Y-%m-%d')}",
                "type": temporal_type,
                "startdate": start_date,
                "enddate": end_date,
            },
        )
        return temporal


class ObservationResource(ModelResource):
    measure = Field(
        column_name="measure",
        attribute="measure",
        widget=MeasureForeignKeyWidget(Measure, field="name"),
    )
    spatialdimension = Field(
        column_name="spatialdimension",
        attribute="spatialdimension",
        widget=SpatialForeignKeyWidget(SpatialDimension, field="code"),
    )
    temporaldimension = Field(
        column_name="temporaldimension",
        attribute="temporaldimension",
        widget=TemporalForeignKeyWidget(TemporalDimension, field="name"),
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # check main error's first on Dataset (instead of row by row)

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
            dfmeasure = pd.DataFrame(list(Measure.objects.values("id", "name")))
            dfspatialdimtype = pd.DataFrame(
                list(SpatialDimensionType.objects.values("id", "name"))
            )
            dftemporaldimtype = pd.DataFrame(
                list(TemporalDimensionType.objects.values("id", "name"))
            )
            dfspatialdim = pd.DataFrame(
                list(
                    SpatialDimension.objects.select_related("type").values(
                        "id", "code", "source_date", "type__name"
                    )
                )
            )
            dftemporaldim = pd.DataFrame(
                list(
                    TemporalDimension.objects.select_related("type").values(
                        "id", "startdate", "type__name"
                    )
                )
            )

            # convert 'spatial_date' to datetime.date format for check
            dataset.append_col(
                tuple([convert_to_date(x) for x in dataset["spatial_date"]]),
                header="source_date",
            )
            dataset.append_col(
                tuple([convert_to_date(x) for x in dataset["temporal_date"]]),
                header="start_date",
            )

            check = {
                "measure_names": {
                    "dataset": dataset,
                    "dfmodel": dfmeasure,
                    "column": ["measure"],
                    "field": ["name"],
                },
                "spatial_types": {
                    "dataset": dataset,
                    "dfmodel": dfspatialdimtype,
                    "column": [
                        "spatial_type",
                    ],
                    "field": [
                        "name",
                    ],
                },
                "temporal_types": {
                    "dataset": dataset,
                    "dfmodel": dftemporaldimtype,
                    "column": [
                        "temporal_type",
                    ],
                    "field": [
                        "name",
                    ],
                },
                "spatial_codes": {
                    "dataset": dataset,
                    "dfmodel": dfspatialdim,
                    "column": [
                        "spatial_code",
                    ],
                    "field": [
                        "code",
                    ],
                },
                "spatial_dates": {
                    "dataset": dataset,
                    "dfmodel": dfspatialdim,
                    "column": [
                        "source_date",
                    ],
                    "field": [
                        "source_date",
                    ],
                },
                "spatial_dim": {
                    "dataset": dataset,
                    "dfmodel": dfspatialdim,
                    "column": ["source_date", "spatial_code", "spatial_type"],
                    "field": ["source_date", "code", "type__name"],
                },
                "temporal_dim": {
                    "dataset": dataset,
                    "dfmodel": dftemporaldim,
                    "column": ["start_date", "temporal_type"],
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

    def before_import_row(self, row, row_number, **kwargs):
        row["value"] = convert_str(row["value"])
        row["spatialdimension"] = "-"
        row["temporaldimension"] = "-"

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with empty value,
        necessary since importfile for Observationmodel allows blank value"""

        if row["value"] in [""]:
            return True
        else:
            return super().skip_row(instance, original, row, import_validation_errors)

    @classmethod
    def get_error_result_class(self):
        """
        Returns a class which has custom formatting of the error.
        Used here to simplify the trace error
        """
        return SimpleError

    class Meta:
        model = Observation
        # use_bulk = True
        # instance_loader_class = CachedInstanceLoader
        skip_unchanged = True
        report_skipped = True
        exclude = ("id", "created_at", "updated_at")
        import_id_fields = ("measure", "spatialdimension", "temporaldimension")
        # Iterate over chunks of CHUNKSIZE objects at once
        chunk_size = CHUNKSIZE
