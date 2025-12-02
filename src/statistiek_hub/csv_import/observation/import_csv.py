import logging
import time
import uuid
from io import IOBase, StringIO

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models.functions import Upper
from pandas import to_numeric
from pandas.core.frame import DataFrame
from pandas.io.parsers import read_csv

from statistiek_hub.csv_import.observation.exceptions import (
    MisMatchTypes,
    MissingColumns,
    MissingValues,
)
from statistiek_hub.csv_import.observation.queries import (
    copy_csv_query,
    create_table_as_query,
    delete_query,
    drop_table_query,
    insert_query,
    update_query,
)
from statistiek_hub.csv_import.observation.result import Result
from statistiek_hub.csv_import.observation.utils import (
    execute_query_and_return_dataframe,
)
from statistiek_hub.models import Observation, SpatialDimension
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.temporal_dimension import TemporalDimension
from statistiek_hub.utils.datetime import convert_to_date

logger = logging.getLogger(__name__)


def _pre_import_check_mandatory_columns(df: DataFrame):
    """
    Check if all columns are present in the dataframe
    """
    logger.info("Check if mandatory columns are present")

    expected = [
        "measure",
        "spatial_code",
        "spatial_type",
        "spatial_date",
        "temporal_type",
        "temporal_date",
        "value",
    ]

    if missing_columns := set(expected) - set(df.columns.to_list()):
        raise MissingColumns(f"Missing column(s): {', '.join(list(missing_columns))}")


def _transform_measure(df: DataFrame):
    """
    Check and transform the measure (str value) into the corresponding Measure pk

    Raises a MissingValues exception if non-existing measures are in dataframe
    """
    df["measure"] = df["measure"].str.upper()
    distinct_uppercase_values = df["measure"].unique()

    measure_qs = Measure.objects.annotate(upper_name=Upper("name")).filter(
        upper_name__in=distinct_uppercase_values
    )

    existing_values = measure_qs.values_list("upper_name", flat=True)

    if missing_values := list(set(distinct_uppercase_values) - set(existing_values)):
        raise MissingValues(f"Missing measures: {', '.join(list(missing_values))}")

    measure_id_map = dict(
        Measure.objects.annotate(upper_name=Upper("name")).values_list(
            "upper_name", "id"
        )
    )
    df["measure_id"] = df["measure"].map(measure_id_map)

    df.drop(columns=["measure"], inplace=True)


def _transform_spatialdim(df: DataFrame):
    """
    Check and transform the spatial dimensions (combined value) into the corresponding SpatialDimension pk

    Raises a MissingValues exception if non-existing spatial dimensions are in dataframe
    """
    df["spatial_code"] = df["spatial_code"].str.upper()
    df["spatial_type"] = df["spatial_type"].str.upper()
    df["spatial_date"] = df["spatial_date"].astype(str).apply(convert_to_date)

    spatialdimension_qs = (
        SpatialDimension.objects.select_related("type")
        .annotate(upper_code=Upper("code"), upper_type_name=Upper("type__name"))
        .values("id", "upper_code", "source_date", "upper_type_name")
    )

    valid_combinations = {
        (row["upper_code"], row["upper_type_name"], row["source_date"])
        for row in spatialdimension_qs
    }

    df_combinations = set(
        zip(df["spatial_code"], df["spatial_type"], df["spatial_date"])
    )

    missing_combinations = df_combinations - valid_combinations

    if missing_combinations:
        missing_list = [
            f"(code='{code}', type='{type_}', date='{date}')"
            for code, type_, date in sorted(missing_combinations)
        ]
        raise MissingValues(
            f"The following spatial dimension combinations do not exist in the database: "
            f"{', '.join(missing_list)}"
        )

    lookup = {
        (row["upper_code"], row["upper_type_name"], row["source_date"]): row["id"]
        for row in spatialdimension_qs
    }

    df["spatialdimension_id"] = df.apply(
        lambda row: lookup[
            (row["spatial_code"], row["spatial_type"], row["spatial_date"])
        ],
        axis=1,
    )

    df.drop(columns=["spatial_code", "spatial_type", "spatial_date"], inplace=True)


def _transform_temporaldim(df: DataFrame):
    """
    Check and transform the temporal dimensions (combined value) into the corresponding TemporalDimension pk

    Raises a MissingValues exception if non-existing temporal dimensions are in dataframe
    """
    df["temporal_type"] = df["temporal_type"].str.upper()
    df["temporal_date"] = df["temporal_date"].astype(str).apply(convert_to_date)

    temporaldimension_qs = (
        TemporalDimension.objects.select_related("type")
        .annotate(upper_type_name=Upper("type__name"))
        .values("id", "startdate", "upper_type_name")
    )

    valid_combinations = {
        (row["upper_type_name"], row["startdate"]) for row in temporaldimension_qs
    }

    df_combinations = set(zip(df["temporal_type"], df["temporal_date"]))

    missing_combinations = df_combinations - valid_combinations

    if missing_combinations:
        missing_list = [
            f"(type='{type_}', date='{date}')"
            for type_, date in sorted(missing_combinations)
        ]
        raise MissingValues(
            f"The following temporal dimension combinations do not exist in the database: "
            f"{', '.join(missing_list)}"
        )

    lookup = {
        (row["upper_type_name"], row["startdate"]): row["id"]
        for row in temporaldimension_qs
    }

    df["temporaldimension_id"] = df.apply(
        lambda row: lookup[(row["temporal_type"], row["temporal_date"])], axis=1
    )

    df.drop(columns=["temporal_type", "temporal_date"], inplace=True)


def _check_measure_temporal_dimension_type_matches(df: DataFrame):
    measure_ids = df["measure_id"].unique().tolist()
    temporaldimension_ids = df["temporaldimension_id"].unique().tolist()

    measure_types = dict(
        Measure.objects.filter(id__in=measure_ids).values_list("id", "temporaltype")
    )
    temporal_types = dict(
        TemporalDimension.objects.filter(id__in=temporaldimension_ids).values_list(
            "id", "type__type"
        )
    )

    df["types_match"] = df.apply(
        lambda row: measure_types.get(row["measure_id"])
        == temporal_types.get(row["temporaldimension_id"]),
        axis=1,
    )

    mismatched_rows = df[~df["types_match"]]

    if not mismatched_rows.empty:
        raise MisMatchTypes(
            f"Found {len(mismatched_rows)} rows with mismatched temporal types"
        )


def pre_import(df: DataFrame):
    """
    Makes sure that all pre import checks and transformations are done
    """
    errors = []

    try:
        _pre_import_check_mandatory_columns(df=df)
    except MissingColumns as e:
        errors.append(str(e))

    try:
        _transform_measure(df=df)
    except MissingValues as e:
        errors.append(str(e))

    try:
        _transform_spatialdim(df=df)
    except MissingValues as e:
        errors.append(str(e))

    try:
        _transform_temporaldim(df=df)
    except MissingValues as e:
        errors.append(str(e))

    try:
        _check_measure_temporal_dimension_type_matches(df=df)
    except MisMatchTypes as e:
        errors.append(str(e))

    if errors:
        raise ValidationError(errors)

    df["value"] = df["value"].astype(str).str.replace(",", ".")
    df["value"] = to_numeric(df["value"], errors="coerce")


def copy_and_sync(df: DataFrame, dry_run: bool = True) -> Result:
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    columns = ", ".join(df.columns)

    table_name = Observation._meta.db_table
    tmp_table_name = f"{table_name}_tmp_{uuid.uuid4().hex[:8]}"

    connection.close()

    result = Result(original=df)

    with transaction.atomic():
        with connection.cursor() as cursor:
            # Create the TMP table
            cursor.execute(
                create_table_as_query.format(
                    table_name=table_name, tmp_table_name=tmp_table_name
                )
            )

            # Copy the CSV into the tmp table
            cursor.copy_expert(
                copy_csv_query.format(table_name=tmp_table_name, columns=columns),
                csv_buffer,
            )

            # Run the update query
            result.updated = execute_query_and_return_dataframe(
                update_query.format(
                    table_name=table_name, tmp_table_name=tmp_table_name
                ),
                cursor,
            )

            # Run the insert query
            result.inserted = execute_query_and_return_dataframe(
                insert_query.format(
                    table_name=table_name, tmp_table_name=tmp_table_name
                ),
                cursor,
            )

            # Run the delete query
            result.deleted = execute_query_and_return_dataframe(
                delete_query.format(
                    table_name=table_name, tmp_table_name=tmp_table_name
                ),
                cursor,
            )

            # Drop the tmp table
            cursor.execute(drop_table_query.format(table_name=tmp_table_name))

            if dry_run:
                logger.info("Dry run enabled, rollback the transaction")
                transaction.set_rollback(True)
            else:
                logger.info("Dry run disabled, commit the transaction")

    return result


def data_to_dataframe(filepath_or_buffer: str | IOBase) -> DataFrame:
    return read_csv(
        filepath_or_buffer=filepath_or_buffer, header=0, sep=";", keep_default_na=False
    )


def import_csv(filepath_or_buffer: str | IOBase, dry_run: bool = True) -> Result:
    """
    Import Observation CSV file
    """
    logger.info("Import Observation CSV started")
    logger.info(f"Dry-run: {"enabled" if dry_run else "disabled"}")
    start_time = time.time()

    df = data_to_dataframe(filepath_or_buffer=filepath_or_buffer)

    pre_import(df=df)
    result = copy_and_sync(df=df, dry_run=dry_run)

    logger.info(
        f"Summary: Inserted {result.total_inserted}, updated {result.total_updated} and deleted {result.total_deleted} row(s)"
    )

    duration = time.time() - start_time
    logger.info(f"Import Observation CSV done in {duration:.2f} seconds")
    return result
