import logging
import time
import uuid
from io import IOBase, StringIO

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models.functions import Upper
from pandas import to_numeric
from pandas.core.frame import DataFrame
from pandas.io.parsers import read_csv

from statistiek_hub.models import Observation, SpatialDimension
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.temporal_dimension import TemporalDimension
from statistiek_hub.utils.datetime import convert_to_date

logger = logging.getLogger(__name__)


class MissingColumns(Exception):
    pass


class MissingValues(Exception):
    pass


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

    if errors:
        raise ValidationError(errors)

    df["value"] = df["value"].astype(str).str.replace(",", ".")
    df["value"] = to_numeric(df["value"], errors="coerce")


def copy_and_sync(df: DataFrame, dry_run: bool = True) -> tuple[int, int, int]:
    df_len = len(df)
    if df_len == 0:
        logger.info("No Observations to update, insert and or delete")
        return 0, 0, 0

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)

    columns = ", ".join(df.columns)

    table_name = Observation._meta.db_table
    tmp_table_name = f"{table_name}_tmp_{uuid.uuid4().hex[:8]}"

    connection.set_autocommit(False)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {tmp_table_name} "
                f"AS TABLE {table_name} WITH NO DATA"
            )

            cursor.copy_expert(
                f"COPY {tmp_table_name} ({columns}) FROM STDIN WITH CSV", csv_buffer
            )

            update_sql = (
                f"UPDATE {table_name} AS org "
                f"SET value = tmp.value, updated_at = now() "
                f"FROM {tmp_table_name} AS tmp "
                f"WHERE org.measure_id = tmp.measure_id AND "
                f"org.temporaldimension_id = tmp.temporaldimension_id AND "
                f"org.spatialdimension_id = tmp.spatialdimension_id AND "
                f"tmp.value IS NOT NULL AND "
                f"org.value != tmp.value"
            )
            cursor.execute(update_sql)
            rows_updated = cursor.rowcount

            insert_sub_query = (
                f"SELECT org.* FROM {table_name} AS org "
                f"WHERE org.measure_id = tmp.measure_id AND "
                f"org.temporaldimension_id = tmp.temporaldimension_id AND "
                f"org.spatialdimension_id = tmp.spatialdimension_id"
            )

            insert_sql = (
                f"INSERT INTO {table_name} (created_at, updated_at, value, measure_id, spatialdimension_id, temporaldimension_id) "
                f"SELECT now() AS created_at, now() AS updated_at, tmp.value, tmp.measure_id, tmp.spatialdimension_id, tmp.temporaldimension_id "
                f"FROM {tmp_table_name} AS tmp "
                f"WHERE NOT EXISTS ({insert_sub_query}) "
                f"AND tmp.value IS NOT NULL"
            )
            cursor.execute(insert_sql)
            rows_inserted = cursor.rowcount

            delete_sql = (
                f"DELETE FROM {table_name} AS org "
                f"USING {tmp_table_name} AS tmp "
                f"WHERE org.measure_id = tmp.measure_id AND "
                f"org.temporaldimension_id = tmp.temporaldimension_id AND "
                f"org.spatialdimension_id = tmp.spatialdimension_id AND "
                f"tmp.value IS NULL"
            )
            cursor.execute(delete_sql)
            rows_deleted = cursor.rowcount

            # Delete the tmp table
            cursor.execute(f"DROP TABLE IF EXISTS {tmp_table_name}")

            if dry_run:
                logger.info("Dry run enabled, rollback the transaction")
                connection.rollback()
            else:
                logger.info("Dry run disabled, commit the transaction")
                connection.commit()

        return rows_inserted, rows_updated, rows_deleted
    finally:
        connection.set_autocommit(True)


def import_csv(
    filepath_or_buffer: str | IOBase, dry_run: bool = True
) -> tuple[int, int, int]:
    """
    Import Observation CSV file
    """
    logger.info("Import Observation CSV started")
    logger.info(f"Dry-run: {"enabled" if dry_run else "disabled"}")
    start_time = time.time()

    df = read_csv(
        filepath_or_buffer=filepath_or_buffer, header=0, sep=";", keep_default_na=False
    )

    pre_import(df=df)
    inserted, updated, deleted = copy_and_sync(df=df, dry_run=dry_run)

    logger.info(
        f"Summary: Inserted {inserted}, updated {updated} and deleted {deleted} row(s)"
    )

    duration = time.time() - start_time
    logger.info(f"Import Observation CSV done in {duration:.2f} seconds")
    return inserted, updated, deleted
