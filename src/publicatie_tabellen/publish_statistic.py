import logging

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet

from publicatie_tabellen.constants_settings import (
    EXCLUDE_KLEURENPALET_SD,
    KLEURENPALET,
    SD_MIN_BEVTOTAAL,
    SD_MIN_WVOORRBAG,
    SP_CODE_AMSTERDAM,
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


def _get_qs_publishstatistic_obs(cleaned_obsmodel, measure_list) -> QuerySet:
    """get queryset from cleaned obs publication model specificly for publishstatistic"""
    queryset = (
        cleaned_obsmodel.objects
        .filter(
            spatialdimensiontype__in=["Wijk", "GGW-gebied", "Gemeente"],
            temporaldimensiontype="Peildatum",
            measure__in = measure_list,
        )
        .annotate(measure_name = F("measure"),)
        .order_by("measure_name", "temporaldimensionyear", "temporaldimensionstartdate")
        .distinct()
        .values('id', 'spatialdimensiontype', 'spatialdimensiondate',
                'spatialdimensioncode', 'spatialdimensionname', 'temporaldimensiontype',
                'temporaldimensionstartdate', 'temporaldimensionenddate',
                'temporaldimensionyear', 'measure_name', 'value')
    )    

    return queryset


def _get_qs_publishstatistic_measure(measuremodel)-> QuerySet:
    """measures exclude kleurenpalet, annotate var from extra_attr json field """
    queryset = (
        measuremodel.objects
        .exclude(**{f"extra_attr__{KLEURENPALET}__in": EXCLUDE_KLEURENPALET_SD})
        .annotate(
            sd_minimum_bevtotaal=Coalesce(
                F(f"extra_attr__{SD_MIN_BEVTOTAAL}"), Value(None)
            ),
            sd_minimum_wvoorrbag=Coalesce(
                F(f"extra_attr__{SD_MIN_WVOORRBAG}"), Value(None)
            ),
            measure_id = F("id"),
        )
        .values("measure_id", "name", "sd_minimum_bevtotaal", "sd_minimum_wvoorrbag")
    )

    return queryset

def _get_df_data_publishstatistic()-> pd.DataFrame:
    """get all observations necessary for calculation of statistic standarddeviation"""

    qsmeasure = _get_qs_publishstatistic_measure(Measure)
    measure_list = qsmeasure.values_list('name', flat=True)
    qsobservation = _get_qs_publishstatistic_obs(PublicationObservation, measure_list)

    if not (qsobservation):
        return pd.DataFrame()

    df_obs = convert_queryset_into_dataframe(qsobservation)
    df_measure = convert_queryset_into_dataframe(qsmeasure)
    df = df_obs.merge(df_measure, how='left', left_on="measure_name", right_on='name')

    return df


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
    df_wijk_ggw = df[df["spatialdimensiontype"].isin(["Wijk", "GGW-gebied"])][
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
    # door het format per variabele kan de standaarddeviatie niet berekend worden -> daarom eerst value omzetten naar float
    _df["value"] = _df["value"].astype(float)

    # split df in wijk en gebied22 - standarddeviation
    _df_wijk = (
        _df[_df["spatialdimensiontype"] == "Wijk"]
        .groupby(["temporaldimensionyear", "measure_id"])
        .agg({"value": "std"})
        .rename(columns={"value": "sd_wijk"})
        .reset_index()
    )
    _df_wijk["bron_wijk"] = "sdbc"

    _df_geb = (
        _df[_df["spatialdimensiontype"] == "GGW-gebied"]
        .groupby(["temporaldimensionyear", "measure_id"])
        .agg({"value": "std"})
        .rename(columns={"value": "sd_geb"})
        .reset_index()
    )
    _df_geb["bron_geb"] = "sdgeb22"

    # std calculation of wijk and geb22 concatenation
    df_wijk_geb = _df_wijk.join(
        _df_geb.set_index(["temporaldimensionyear", "measure_id"]),
        on=["temporaldimensionyear", "measure_id"],
        how="outer",
    )
    df_wijk_geb.reset_index(inplace=True)

    # coalesce of std wijk and geb22
    df_wijk_geb["standarddeviation"] = df_wijk_geb["sd_wijk"].combine_first(
        df_wijk_geb["sd_geb"]
    )
    # noteren waar de sd vandaan komt als source
    df_wijk_geb["source"] = df_wijk_geb["bron_wijk"].combine_first(
        df_wijk_geb["bron_geb"]
    )

    return df_wijk_geb[
        ["temporaldimensionyear", "measure_id", "standarddeviation", "source"]
    ]


def publishstatistic() -> tuple:
    """select observations and calculate statistic
    exclude measures with:
    -kleurenpalet 9: geen kleuren /absolute aantallen;
    -kleurenpalet 4: wit"
    return: tuple(string, django.contrib.messages)
    """

    logger.info("get all data necessary for calculation of statistic standarddeviation")    
    df = _get_df_data_publishstatistic()

    if len(df) == 0:
        return (
            f"There are no observations standarddeviation could be applied to",
            messages.ERROR,
        )

    qsmin = get_qs_for_bevmin_wonmin(Observation)
    dfmin = convert_queryset_into_dataframe(qsmin)

    logger.info("aanmaken df met gemiddelde")
    df_mean = _select_df_mean(df)

    logger.info("berekening standaarddeviatie op wijk en geb22")
    df_wijk_ggw = _select_df_wijk_ggw(df)
    _hulp1 = set_small_regions_to_nan_if_minimum(dfmin, "BEVTOTAAL", df_wijk_ggw)
    _hulp2 = set_small_regions_to_nan_if_minimum(dfmin, "WVOORRBAG", _hulp1)
    _hulp3 = _sd_berekening(_hulp2)

    logger.info("alles samenvoegen tot statistic df")
    dfstatistic = df_mean.join(
        _hulp3.set_index(["temporaldimensionyear", "measure_id"]),
        on=["temporaldimensionyear", "measure_id"],
        how="left",
    ).replace({np.nan: None})
    measure_no_sd = dfstatistic[dfstatistic["standarddeviation"].isna()][
        "measure_name"
    ].values
    # if there is no standarddeviation -> remove record
    dfstatistic.dropna(subset=["standarddeviation"], inplace=True)
    dfstatistic.rename(columns={"measure_name": "measure"}, inplace=True)

    # gemiddelde en std afronden op 3 decimalen -> set on the model field
    try:
        truncate(PublicationStatistic)
        copy_dataframe(dfstatistic, PublicationStatistic)
        extra = (
            f", WARNING Not included: no standarddeviation for {measure_no_sd}"
            if len(measure_no_sd) > 0
            else ""
        )
        return (
            f"All records for publication-statistic are imported{extra}",
            messages.SUCCESS,
        )
    except:  # error
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR)
