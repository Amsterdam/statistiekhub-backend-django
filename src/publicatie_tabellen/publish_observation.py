import logging

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db import connection
from django.db.models import F
from django.db.models.query import QuerySet

from publicatie_tabellen.models import PublicationObservation
from publicatie_tabellen.utils import (
    convert_queryset_into_dataframe,
    copy_dataframe,
    round_to_base,
)
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_publishobservation(obsmodel) -> QuerySet:
    """ get queryset from obsmodel specificly for publishobservations"""

    queryset = obsmodel.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
                .annotate(spatialdimensiontype=F('spatialdimension__type__name'), 
                        spatialdimensiondate=F('spatialdimension__source_date'), 
                        spatialdimensioncode=F('spatialdimension__code'), 
                        spatialdimensionname=F('spatialdimension__name'),
                        temporaldimensiontype=F('temporaldimension__type__name'),  
                        temporaldimensionstartdate=F('temporaldimension__startdate'),
                        temporaldimensionenddate=F('temporaldimension__enddate'),  
                        temporaldimensionyear=F('temporaldimension__year'), 
                        sensitive=F('measure__sensitive'),
                        unit=F('measure__unit__name'),
                        decimals = F('measure__decimals'),
                        measure_name = F('measure__name')
                        ).defer("created_at", "updated_at")
    return queryset
    
def _apply_sensitive_rules(value, unit):
    """ change value by rule depending on unit"""
            
    if pd.isna(value) or value==None:
        return None

    match unit:
        case 'aantal':
            # afronden op 5 tallen
            if 0 < value < 5:
                return 5
            else:
                return round_to_base(value, 5)

        case 'percentage':
            # afronden naar 90%

            if value >= 90:
                return 90
    # else
    return value

def _get_df_with_filterrule(measure: Measure) -> pd.DataFrame:
    """ apply sql db_function public.apply_filter on measure 
        return: dataframe with value corrected by filterrule """
    
    if pd.isna(measure.filter.value_new):
        value_new = 'Null'
    else:
        value_new = measure.filter.value_new

    raw_query =  f"select (public.apply_filter ({measure.id}, '{measure.filter.rule}', {value_new} )).*" 

    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        measure_obs = cursor.fetchall()

    def _transform_results_to_df(results: list) -> pd.DataFrame:
        """ Transform the query results into a pandas Dataframe
        return: dataframe returned from apply_filter query"""

        # Create DataFrame
        _df = pd.DataFrame(results, columns=['created_at', 'update_at', 'id', 'value', 'measure_id', 'spatialdimension_id', 'temporaldimension_id'])
        # drop colums
        _df.drop(['created_at', 'update_at', 'id'], axis=1, inplace=True)

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

    # select observations
    qsobservation = _get_qs_publishobservation(Observation)
    qscalcobs = _get_qs_publishobservation(ObservationCalculated)
    print('-----------qscalcobs', qscalcobs)

    #-- set queryset observations into dataframe
    df_obs = convert_queryset_into_dataframe(qsobservation)
    df_calc = convert_queryset_into_dataframe(qscalcobs)
    df = pd.concat([df_obs, df_calc], ignore_index=True)
    # TODO weg alleen voor testen
    df['value_org'] = df['value']
    df['value_new'] = df['value']

    # get all measures
    qsmeasure = Measure.objects.all()

    truncate(PublicationObservation)
    for measure in qsmeasure:
        if not (measure.name == 'BEVMIGONB_P'):
            continue
        print('---measure', measure)

        # select measure df
        mdf = df[df['measure_id']==measure.id].copy()
        print(mdf[['measure_name', 'measure_id', 'unit', 'decimals', 'sensitive', 'value', 'value_new', 'value_org', 'spatialdimension_id', 'temporaldimension_id' ]])

        if hasattr(measure,"filter"):        
            dfobs = _get_df_with_filterrule(measure)

            # update mdf with new values from dfobs
            mdf=mdf.merge(dfobs,
                    on=['measure_id', 'spatialdimension_id', 'temporaldimension_id'],
                    how='left',
                    suffixes=("_x", None))
            print(mdf)
            mdf.drop("value_x" ,axis=1 ,inplace=True)

            logger.info("filterrule applied")
            print(mdf[['measure_name', 'measure_id', 'unit', 'decimals', 'sensitive', 'value', 'value_new', 'value_org', 'spatialdimension_id', 'temporaldimension_id' ]])

        if  measure.sensitive:
            mdf["value_new"]= mdf.apply(lambda x: _apply_sensitive_rules(x.value, x.unit), axis=1)  
            logger.info("sensitiverules applied")
            print(mdf[['measure_name', 'measure_id', 'unit', 'decimals', 'sensitive', 'value', 'value_new', 'value_org', 'spatialdimension_id', 'temporaldimension_id' ]])

        # apply decimalen
        mdf["value"]= mdf.apply(lambda x: round(x.value_new, x.decimals), axis=1) 
        logger.info("decimals set") 
        print(mdf[['measure_name', 'measure_id', 'unit', 'decimals', 'sensitive', 'value', 'value_new', 'value_org', 'spatialdimension_id', 'temporaldimension_id' ]])

        # set np.nan to None for postgres db -> OR TODO remove nan values from mdf because not necessary
        mdf['value'] = mdf['value'].replace(np.nan, None)
        mdf.rename(columns={"measure_name": "measure"}, inplace=True)
        # save measure df in Publishobservation
        copy_dataframe(mdf, PublicationObservation)

    try:
        return (f"All records for publish-observation are imported", messages.SUCCESS)
    except:
        print(f'------------{measure} niet aanwezig in data')
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR) 

    
