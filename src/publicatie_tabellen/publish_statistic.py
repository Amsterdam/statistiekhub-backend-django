import logging

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet

from publicatie_tabellen.models import PublicationStatistic
from publicatie_tabellen.utils import convert_queryset_into_dataframe, copy_dataframe
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_publishstatistic(obsmodel) -> QuerySet:
    """ get queryset from obsmodel specificly for publishstatistic"""
    queryset = obsmodel.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
                .filter(spatialdimension__type__name__in = ['Wijk','GGW-gebied', 'Gemeente'],
                        temporaldimension__type__name = 'Peildatum')\
                .exclude(measure__extra_attr__BBGA_kleurenpalet__in = [9,4] )\
                .annotate(spatialdimensiondate = F('spatialdimension__source_date'), 
                        spatialdimensioncode = F('spatialdimension__code'),
                        spatialdimensiontypename = F('spatialdimension__type__name'),
                        temporaldimensiontype = F('temporaldimension__type__name'),  
                        temporaldimensionstartdate = F('temporaldimension__startdate'),
                        temporaldimensionyear = F('temporaldimension__year'),
                        sd_minimum_bevtotaal = Coalesce(F('measure__extra_attr__BBGA_sd_minimum_bev_totaal'), Value(None)),
                        sd_minimum_wvoorrbag = Coalesce(F('measure__extra_attr__BBGA_sd_minimum_wvoor_bag'), Value(None)),
                        measure_name = F('measure__name')
                        )\
                    .order_by('measure', 'temporaldimensionyear','temporaldimensionstartdate')\
                    .defer("created_at", "updated_at")\
                    .distinct()
    return queryset


def _get_qs_for_bevmin_wonmin(obsmodel = Observation) -> QuerySet:
    """ get queryset of observations with only measures, bevtotaal and wvoorrbag, 
    for spatialdimensiontype wijk and ggw-gebied 
    and temporaldimensiontype 'Peildatum'
    """
    queryset = obsmodel.objects.select_related('measure', 'spatialdimension', 'temporaldimension')\
                .filter(measure__name__in = ["BEVTOTAAL", "WVOORRBAG"], 
                        spatialdimension__type__name__in=['Wijk','GGW-gebied'],
                        temporaldimension__type__name = 'Peildatum')\
                .annotate(spatialdimensiondate = F('spatialdimension__source_date'), 
                        spatialdimensioncode = F('spatialdimension__code'),
                        temporaldimensionstartdate = F('temporaldimension__startdate'),
                        temporaldimensionyear = F('temporaldimension__year'),
                        measure_name = F('measure__name')
                        )\
                .order_by('measure','temporaldimension__year','temporaldimension__startdate')\
                .defer("created_at", "updated_at")\
                .distinct()
    return queryset


def _select_df_mean(df: pd.DataFrame) -> pd.DataFrame:
    """ Mean of a measure is the city-avarage, thus spatialdimensioncode '0363' Amsterdam. """
    df_mean = df[df['spatialdimensioncode'] == '0363']\
                        [[ "spatialdimensiondate", 
                            "temporaldimensiontype", 
                            "temporaldimensionstartdate",
                            "temporaldimensionyear", 
                            "measure_id", "measure_name", "value",]]\
                        .rename(columns={'value':'average'}).dropna(subset=['average']).copy()
    return df_mean


def _select_df_wijk_ggw(df: pd.DataFrame) -> pd.DataFrame:
    """ Select only spatialdimension 'Wijk' and 'GGW-gebied' """
    #TODO wat te doen met variabelen die geen std hebben omdat geen wijk en/of 22 gebied?   
    df_wijk_ggw = df[df['spatialdimensiontypename'].isin(['Wijk','GGW-gebied'])]\
                        [[ "spatialdimensiondate",
                            "spatialdimensiontypename", 
                            "spatialdimensioncode", 
                            "temporaldimensiontype", 
                            "temporaldimensionstartdate",
                            "temporaldimensionyear",
                            "sd_minimum_bevtotaal",
                            "sd_minimum_wvoorrbag",
                            "measure_id", "measure_name", "value",]].copy()
    return df_wijk_ggw


def _set_small_regions_to_nan_if_minimum(dfmin: pd.DataFrame, var_min: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    """ set region value to np.nan if var_min is less than minimum_value :
        remove value observation if sd_minimum_bevtotaal or sd_minimum_wvoorrbag condition is not met """

    # get the values of bevtotaal or wvoorrbag
    _df_var_min= dfmin[(dfmin['measure_name'] == var_min)][["temporaldimensionyear", "spatialdimensiondate", "spatialdimensioncode", "value"]] 

    if len(_df_var_min) == 0:
        return dataframe

    hulp = dataframe.join(_df_var_min.rename(columns={"value": 'varc'})\
                        .set_index(["temporaldimensionyear", "spatialdimensiondate", "spatialdimensioncode"]),\
                                on=["temporaldimensionyear", "spatialdimensiondate", "spatialdimensioncode"], how='left')\
                                .replace({None: np.nan})
    
    #'value' vervangen door onbekend als te klein
    minimum_value = f"sd_minimum_{var_min.lower()}"
    hulp.loc[(hulp['varc'] < hulp[minimum_value]), "value"] = np.nan

    return hulp.drop('varc', axis=1)


def _sd_berekening(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    berekening standaarddeviatie op wijk en geb22 niveau
    return: dataframe
    'standarddeviation':= wijk-std if wijkstd exists else ggwstd
    'source':= wijk-source if wijksource exists else ggwsource 
    """
    _df = dataframe.dropna(subset=['value']).copy()
    #door het format per variabele kan de standaarddeviatie niet berekend worden -> daarom eerst value omzetten naar float
    _df['value'] = _df['value'].astype(float)       

    # split df in wijk en gebied22 - standarddeviation
    _df_wijk = _df[_df['spatialdimensiontypename'] == 'Wijk'].groupby(['temporaldimensionyear',"measure_id"]).agg({'value': 'std'}).rename(columns={'value': 'sd_wijk'}).reset_index()
    _df_wijk["bron_wijk"] = 'sdbc'

    _df_geb = _df[_df['spatialdimensiontypename'] == 'GGW-gebied'].groupby(['temporaldimensionyear',"measure_id"]).agg({'value': 'std'}).rename(columns={'value': 'sd_geb'}).reset_index()
    _df_geb["bron_geb"] = 'sdgeb22'

    # std calculation of wijk and geb22 concatenation
    df_wijk_geb = _df_wijk.join(_df_geb.set_index(['temporaldimensionyear', "measure_id"]), on=['temporaldimensionyear', "measure_id"], how ='outer')   
    df_wijk_geb.reset_index(inplace=True)    
    
    # coalesce of std wijk and geb22
    df_wijk_geb['standarddeviation'] = df_wijk_geb['sd_wijk'].combine_first(df_wijk_geb['sd_geb'])
    # noteren waar de sd vandaan komt als source
    df_wijk_geb["source"] = df_wijk_geb["bron_wijk"].combine_first(df_wijk_geb["bron_geb"]) 

    return df_wijk_geb[["temporaldimensionyear","measure_id","standarddeviation","source"]]


def publishstatistic() -> tuple:
    """select observations and calculate statistic
    exclude measures with:
    -kleurenpalet 9: geen kleuren /absolute aantallen; 
    -kleurenpalet 4: wit"
    return: tuple(string, django.contrib.messages)
    """

    logger.info('get all data necessary for calculation of statistic standarddeviation')
    qsobservation = _get_qs_publishstatistic(Observation)
    qscalcobs = _get_qs_publishstatistic(ObservationCalculated)

    if not (qsobservation or qscalcobs):
        return (f"There are no observations standarddeviation could be applied to", messages.ERROR)

    df_obs = convert_queryset_into_dataframe(qsobservation)
    df_calc = convert_queryset_into_dataframe(qscalcobs)
    df = pd.concat([df_obs, df_calc], ignore_index=True)

    qsmin = _get_qs_for_bevmin_wonmin(Observation)
    dfmin = convert_queryset_into_dataframe(qsmin)

    logger.info('aanmaken df met gemiddelde')
    df_mean = _select_df_mean(df) 

    logger.info('berekening standaarddeviatie op wijk en geb22')
    df_wijk_ggw = _select_df_wijk_ggw(df)
    _hulp1  = _set_small_regions_to_nan_if_minimum(dfmin, 'BEVTOTAAL', df_wijk_ggw)
    _hulp2 = _set_small_regions_to_nan_if_minimum(dfmin, 'WVOORRBAG', _hulp1)
    _hulp3 = _sd_berekening(_hulp2)

    logger.info('alles samenvoegen tot statistic df')
    dfstatistic = df_mean.join(_hulp3.set_index(["temporaldimensionyear","measure_id"]), on=["temporaldimensionyear", "measure_id"], how='left').replace({np.nan: None})
    measure_no_sd = dfstatistic[dfstatistic['standarddeviation'].isna()]['measure_name'].values
    # if there is no standarddeviation -> remove record
    dfstatistic.dropna(subset=['standarddeviation'], inplace=True)
    dfstatistic.rename(columns={"measure_name": "measure"}, inplace=True)

    # gemiddelde en std afronden op 3 decimalen -> set on the model field
    try:
        truncate(PublicationStatistic)
        copy_dataframe(dfstatistic, PublicationStatistic)
        extra =  f", WARNING Not included: no standarddeviation for {measure_no_sd}" if len(measure_no_sd) > 0 else ''
        return (f"All records for publication-statistic are imported{extra}", messages.SUCCESS)
    except: # error
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR)
