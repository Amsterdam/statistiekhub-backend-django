import logging

import pandas as pd
from django.contrib import messages
from django.db import connection
from django.db.models import F
from django.db.models.query import QuerySet

from publicatie_tabellen.models import PublicationObservation
from publicatie_tabellen.utils import (
    convert_queryset_into_dataframe,
    copy_dataframe,
    get_qs_for_bevmin_wonmin,
    round_to_base,
    round_to_decimal,
    set_small_regions_to_nan_if_minimum,
)
from referentie_tabellen.models import SpatialDimensionType
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_publishobservation(obsmodel, measure) -> QuerySet:
    """get queryset from obsmodel specificly for publishobservations"""

    queryset = (
        obsmodel.objects.select_related(
            "measure",
            "spatialdimension",
            "temporaldimension",
            "measure__unit",
            "spatialdimension__type",
            "temporaldimension__type",
        )
        .filter(measure=measure)
        .annotate(
            spatialdimensiontype=F("spatialdimension__type__name"),
            spatialdimensiondate=F("spatialdimension__source_date"),
            spatialdimensioncode=F("spatialdimension__code"),
            spatialdimensionname=F("spatialdimension__name"),
            temporaldimensiontype=F("temporaldimension__type__name"),
            temporaldimensionstartdate=F("temporaldimension__startdate"),
            temporaldimensionenddate=F("temporaldimension__enddate"),
            temporaldimensionyear=F("temporaldimension__year"),
            sensitive=F("measure__sensitive"),
            unit=F("measure__unit__name"),
            decimals=F("measure__decimals"),
            measure_name=F("measure__name"),
        )
        .defer("created_at", "updated_at")
    )
    return queryset


def _apply_sensitive_rules(value, unit):
    """change value by rule depending on unit"""

    if pd.isna(value) or value == None:
        return None

    match unit:
        case "aantal":
            # afronden op 5 tallen
            if 0 < value < 5:
                return 5
            else:
                return round_to_base(value, 5)

        case "percentage":
            # afronden naar 90%
            if value >= 90:
                return 90

    return value


def _get_df_with_filterrule(measure: Measure) -> pd.DataFrame:
    """apply sql db_function public.apply_filter on measure
    return: dataframe with value corrected by filterrule"""

    value_new = (
        "Null" if pd.isna(measure.filter.value_new) else measure.filter.value_new
    )
    raw_query = f"select (public.apply_filter ({measure.id}, '{measure.filter.rule}', {value_new} )).*"

    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        measure_obs = cursor.fetchall()

    def _transform_results_to_df(results: list) -> pd.DataFrame:
        """Transform the query results into a pandas Dataframe
        return: dataframe returned from apply_filter query"""

        _df = pd.DataFrame(
            results,
            columns=[
                "created_at",
                "update_at",
                "id",
                "value",
                "measure_id",
                "spatialdimension_id",
                "temporaldimension_id",
            ],
        )
        _df.drop(["created_at", "update_at", "id"], axis=1, inplace=True)
        return _df

    dfobs = _transform_results_to_df(measure_obs)

    return dfobs


def publishobservation() -> tuple:
    """select observations and change value depending on measure attributtes
    -   filterrule -> apply the measure filterrule from  model  Filter to value
    -   sensitive -> apply sensitive_rules to value
    -   decimals ->  apply Rounding on measure set decimals to value

    Save new values to Publishobservation-model
    return: tuple(string, django.contrib.messages)
    """

    # get BEVTOTAAL for all types for sensitive rule 1: small regions to np.nan
    spatialdimtypes = SpatialDimensionType.objects.all().values_list("name", flat=True)
    qsmin = get_qs_for_bevmin_wonmin(Observation, measures=["BEVTOTAAL",], spatialdimensiontypes=spatialdimtypes)
    dfmin = convert_queryset_into_dataframe(qsmin)

    truncate(PublicationObservation)
    qsmeasure = Measure.objects.all()
    measure_no_data = []

    for measure in qsmeasure:
        # select observations
        qsobservation = _get_qs_publishobservation(Observation, measure)
        if len(qsobservation) == 0:
            qsobservation = _get_qs_publishobservation(ObservationCalculated, measure)
        mdf = convert_queryset_into_dataframe(qsobservation)

        if len(mdf) == 0:
            measure_no_data.append(measure.name)
            continue
        
        logger.info(f"selected observations for {measure}: {len(mdf)}")
        if hasattr(measure, "filter"):
            dfobs = _get_df_with_filterrule(measure)

            # update mdf with new values from dfobs
            mdf = mdf.merge(
                dfobs,
                on=["measure_id", "spatialdimension_id", "temporaldimension_id"],
                how="left",
                suffixes=("_x", None),
            )
            mdf.drop("value_x", axis=1, inplace=True)

            logger.info(f"filterrule {measure.filter.rule} applied")

        if measure.sensitive:
            mdf["value"] = mdf.apply(
                lambda x: _apply_sensitive_rules(x.value, x.unit), axis=1
            )
            logger.info("sensitiverules applied")
            # apply rule 1: Over gebieden met minder dan 50 inwoners rapporteren we geen privacygevoelige indicatoren
            mdf = set_small_regions_to_nan_if_minimum(dfmin, "BEVTOTAAL", mdf, minimum_value=50)
            logger.info("sensitive less 50 inwoners applied")

        # remove the by filter and sensitive introduced np.nan values
        mdf.dropna(subset=['value'], inplace=True)

        if len(mdf) == 0:
            measure_no_data.append(measure.name)
            continue
        
        # round value to decimals
        mdf["value"] = mdf.apply(lambda x: round_to_decimal(x.value, x.decimals), axis=1)
        logger.info("decimals are set")

        mdf.rename(columns={"measure_name": "measure"}, inplace=True)
        # REMARK: saving an int(= zero decimal) into a floatfield will add a .0 to the int.
        copy_dataframe(mdf, PublicationObservation)

    extra = (
        f", WARNING Not included: there aren't any observations for measure's: {measure_no_data}"
        if len(measure_no_data) > 0
        else ""
    )
    return (
        f"All records for publication-observation are imported{extra}",
        messages.SUCCESS,
    )
