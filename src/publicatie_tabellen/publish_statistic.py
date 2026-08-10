import logging

import pandas as pd
from django.contrib import messages
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet

from publicatie_tabellen.constants_settings import (
    EXCLUDE_KLEURENPALET_SD,
    KLEURENPALET,
    MEASURE_BEVTOTAAL,
    MEASURE_WVOORRBAG,
    SD_GGW_LABEL,
    SD_MIN_BEVTOTAAL,
    SD_MIN_WVOORRBAG,
    SD_WIJK_LABEL,
    SP_CODE_AMSTERDAM,
    SPATIAL_DIMENSION_GEMEENTE,
    SPATIAL_DIMENSION_GGW,
    SPATIAL_DIMENSION_WIJK,
    TEMPORAL_DIMENSIONTYPE_PEILDATUM,
)
from publicatie_tabellen.models import PublicationObservation, PublicationStatistic
from publicatie_tabellen.utils import (
    convert_queryset_into_dataframe,
    copy_dataframe,
    get_qs_for_bevmin_wonmin,
    set_small_regions_to_nan_if_minimum,
)
from statistiek_hub.models.observation import Measure, Observation
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)

PUBLISHSTATISTIC_MEASURE_BATCH_SIZE = 50


def _get_qs_publishstatistic_obs_all(cleaned_obsmodel, measure_names: list[str] | None = None) -> QuerySet:
    """Get cleaned obs rows needed for publishstatistic, optionally limited to measures."""
    queryset = cleaned_obsmodel.objects.filter(
        spatialdimensiontype__in=[
            SPATIAL_DIMENSION_WIJK,
            SPATIAL_DIMENSION_GGW,
            SPATIAL_DIMENSION_GEMEENTE,
        ],
        temporaldimensiontype=TEMPORAL_DIMENSIONTYPE_PEILDATUM,
    )

    if measure_names is not None:
        queryset = queryset.filter(measure__in=measure_names)

    queryset = (
        queryset.annotate(
            measure_name=F("measure"),
        )
        .order_by("measure_name", "temporaldimensionyear", "temporaldimensionstartdate")
        .distinct()
        .values(
            "id",
            "spatialdimensiontype",
            "spatialdimensiondate",
            "spatialdimensioncode",
            "spatialdimensionname",
            "temporaldimensiontype",
            "temporaldimensionstartdate",
            "temporaldimensionenddate",
            "temporaldimensionyear",
            "measure_name",
            "value",
        )
    )

    return queryset


def _iter_measure_batches(measures: list[dict], batch_size: int):
    """Yield contiguous batches of measure dictionaries."""
    for start in range(0, len(measures), batch_size):
        yield measures[start : start + batch_size]


def _get_qs_publishstatistic_measure() -> QuerySet:
    """measures exclude kleurenpalet, annotate var from extra_attr json field"""
    queryset = (
        Measure.objects.filter(extra_attr__has_key=KLEURENPALET)  # only objects where the key exists
        .exclude(**{f"extra_attr__{KLEURENPALET}__in": EXCLUDE_KLEURENPALET_SD})
        .annotate(
            sd_minimum_bevtotaal=Coalesce(F(f"extra_attr__{SD_MIN_BEVTOTAAL}"), Value(None)),
            sd_minimum_wvoorrbag=Coalesce(F(f"extra_attr__{SD_MIN_WVOORRBAG}"), Value(None)),
            measure_id=F("id"),
        )
        .values("measure_id", "name", "sd_minimum_bevtotaal", "sd_minimum_wvoorrbag")
    )

    return queryset


def _select_df_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Mean of a measure is the city-avarage, thus spatialdimensioncode '0363' Amsterdam."""
    df_mean = (
        df[df["spatialdimensioncode"] == SP_CODE_AMSTERDAM][
            [
                "spatialdimensiondate",
                "temporaldimensiontype",
                "temporaldimensionstartdate",
                "temporaldimensionyear",
                "measure_id",
                "measure_name",
                "value",
            ]
        ]
        .rename(columns={"value": "average"})
        .dropna(subset=["average"])
        .copy()
    )
    return df_mean


def _select_df_wijk_ggw(df: pd.DataFrame) -> pd.DataFrame:
    """Select only spatialdimension 'Wijk' and 'GGW-gebied'"""
    # TODO wat te doen met variabelen die geen std hebben omdat geen wijk en/of 22 gebied?
    df_wijk_ggw = df[df["spatialdimensiontype"].isin([SPATIAL_DIMENSION_WIJK, SPATIAL_DIMENSION_GGW])][
        [
            "spatialdimensiondate",
            "spatialdimensiontype",
            "spatialdimensioncode",
            "temporaldimensiontype",
            "temporaldimensionstartdate",
            "temporaldimensionyear",
            "sd_minimum_bevtotaal",
            "sd_minimum_wvoorrbag",
            "measure_id",
            "measure_name",
            "value",
        ]
    ].copy()
    return df_wijk_ggw


def _sd_berekening(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    berekening standaarddeviatie op wijk en geb22 niveau
    return: dataframe
    'standarddeviation':= wijk-std if wijkstd exists else ggwstd
    'source':= wijk-source if wijksource exists else ggwsource
    """
    _df = dataframe.dropna(subset=["value"]).copy()
    # door het format per variabele kan de standaarddeviatie niet berekend worden,
    # daarom eerst value omzetten naar float
    _df["value"] = _df["value"].astype(float)

    # split df in wijk en gebied22 - standarddeviation
    _df_wijk = (
        _df[_df["spatialdimensiontype"] == SPATIAL_DIMENSION_WIJK]
        .groupby(["temporaldimensionyear", "measure_id"])
        .agg({"value": "std"})
        .rename(columns={"value": "sd_wijk"})
        .reset_index()
    )
    _df_wijk["bron_wijk"] = SD_WIJK_LABEL

    _df_geb = (
        _df[_df["spatialdimensiontype"] == SPATIAL_DIMENSION_GGW]
        .groupby(["temporaldimensionyear", "measure_id"])
        .agg({"value": "std"})
        .rename(columns={"value": "sd_geb"})
        .reset_index()
    )
    _df_geb["bron_geb"] = SD_GGW_LABEL

    # std calculation wijk and geb22 concatenation
    df_wijk_geb = _df_wijk.join(
        _df_geb.set_index(["temporaldimensionyear", "measure_id"]),
        on=["temporaldimensionyear", "measure_id"],
        how="outer",
    )

    # coalesce of std wijk and geb22
    df_wijk_geb["standarddeviation"] = df_wijk_geb["sd_wijk"].combine_first(df_wijk_geb["sd_geb"])
    # noteren waar de sd vandaan komt als source
    df_wijk_geb["source"] = df_wijk_geb["bron_wijk"].combine_first(df_wijk_geb["bron_geb"])

    return df_wijk_geb[["temporaldimensionyear", "measure_id", "standarddeviation", "source"]]


def _build_df_statistic(df: pd.DataFrame, dfmin: pd.DataFrame) -> pd.DataFrame:
    """Build publication statistic dataframe for one measure."""
    df_mean = _select_df_mean(df)
    df_wijk_ggw = _select_df_wijk_ggw(df)
    df_filtered = set_small_regions_to_nan_if_minimum(dfmin, MEASURE_BEVTOTAAL, df_wijk_ggw)
    df_filtered = set_small_regions_to_nan_if_minimum(dfmin, MEASURE_WVOORRBAG, df_filtered)
    df_sd = _sd_berekening(df_filtered)

    return df_mean.join(
        df_sd.set_index(["temporaldimensionyear", "measure_id"]),
        on=["temporaldimensionyear", "measure_id"],
        how="left",
    )


def publishstatistic() -> tuple:
    """select observations and calculate statistic
    exclude measures with:
    -kleurenpalet 9: geen kleuren /absolute aantallen;
    -kleurenpalet 4: wit"
    return: tuple(string, django.contrib.messages)
    """

    logger.info("get data necessary for calculation of statistic standarddeviation")
    qsmeasure = _get_qs_publishstatistic_measure()
    measure_rows = list(qsmeasure)

    qsmin = get_qs_for_bevmin_wonmin(Observation)
    dfmin = convert_queryset_into_dataframe(qsmin)
    truncate(PublicationStatistic)
    measure_no_sd: list[str] = []

    for measure_batch in _iter_measure_batches(measure_rows, PUBLISHSTATISTIC_MEASURE_BATCH_SIZE):
        batch_names = [measure["name"] for measure in measure_batch]
        # Build only the metadata DataFrame needed for this batch to lower peak memory usage.
        df_measure_batch = pd.DataFrame.from_records(measure_batch)

        qsobservation_batch = _get_qs_publishstatistic_obs_all(PublicationObservation, batch_names)
        df_obs_batch = convert_queryset_into_dataframe(qsobservation_batch)

        if df_obs_batch.empty:
            measure_no_sd.extend(batch_names)
            del df_measure_batch, df_obs_batch
            continue

        df_all = df_obs_batch.merge(df_measure_batch, how="left", left_on="measure_name", right_on="name")
        grouped_by_measure = {name: group for name, group in df_all.groupby("measure_name")}

        for measure in measure_batch:
            df = grouped_by_measure.get(measure["name"], pd.DataFrame())

            if df.empty:
                measure_no_sd.append(measure["name"])
                continue

            logger.info("aanmaken df met gemiddelde voor %s", measure["name"])
            logger.info("berekening standaarddeviatie op wijk en geb22")
            dfstatistic = _build_df_statistic(df, dfmin)

            if dfstatistic.empty:
                # if there is no standarddeviation -> no save
                measure_no_sd.append(measure["name"])
                continue

            # if there is no standarddeviation for specific temporaldimension -> remove record
            dfstatistic = dfstatistic.dropna(subset=["standarddeviation"])
            dfstatistic = dfstatistic.rename(columns={"measure_name": "measure"})

            # gemiddelde en std afronden op 3 decimalen -> set on the model field
            copy_dataframe(dfstatistic, PublicationStatistic)

        # Explicitly release references to batch-scoped DataFrames.
        del df_measure_batch, df_obs_batch, df_all, grouped_by_measure

    extra = f", WARNING Not included: no standarddeviation for {measure_no_sd}" if len(measure_no_sd) > 0 else ""

    return (
        f"All records for publication-statistic are imported{extra}",
        messages.SUCCESS,
    )
