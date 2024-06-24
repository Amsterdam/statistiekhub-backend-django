import logging

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db.models.query import QuerySet
from django.db.models.functions import Round
from django.db import connection
from django.db.models import F

from publicatie_tabellen.models import PublicationObservation

from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_obs_publishobservation(obsmodel) -> QuerySet:
    """ get queryset from obsmodel specificly for publishobservations"""
    # select observations
    obs = obsmodel.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
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
                        value_org= F('value'),
                        value_new = Round('value', precision='measure__decimals'),
                        measure_name = F('measure__name')
                        ).defer("created_at", "updated_at")
    return obs

def _round_to_base(x, base=5):
    """ round up / down to base """
    return base * round(x/base)
    
def _apply_sensitive_rules(value,  unit) -> float:
    """ change value by rule depending on unit"""

    match unit:
        case 'aantal':
            # afronden op 5 tallen
            if 0 < value < 5:
                return 5
            else:
                return _round_to_base(value, 5)

        case 'percentage':
            # afronden naar 90%
            if value >= 90:
                return 90
    # else
    return value


def publishobservation() -> tuple:
    """select observations and change value depending on measure attributtes
    -   filterrule -> apply the measure filterrule from  model  Filter to value
    -   sensitive -> apply sensitive_rules to value
    -   decimals ->  apply Rounding on measure set decimals to value

    Save new values to Publishobservation-model
    return: tuple(string, django.contrib.messages)
    """

    # select observations
    qsobservation = _get_qs_obs_publishobservation(Observation)
    qscalcobs = _get_qs_obs_publishobservation(ObservationCalculated)
    print('-----------qscalcobs', qscalcobs)

    #-- set queryset observations into dataframe # qsobservation._fields
    df_obs = pd.DataFrame(list(qsobservation.values()), columns=qsobservation._fields)
    df_calc =pd.DataFrame(list(qscalcobs.values()), columns=qscalcobs._fields)
    print(f'------------- df obs {df_obs.head()}, {df_obs.columns}')
    print('------------- df calc', df_calc.head())
    df = pd.concat([df_obs, df_calc], ignore_index=True)

    # get all measures
    qsmeasure = Measure.objects.all()
    print('----------lengte-qsmeasure:', len(qsmeasure))

    truncate(PublicationObservation)
    for measure in qsmeasure:
        if not (measure.name == 'BEVMIGONB_P'):
            continue
        print('---measure', measure)

        # select measure df
        mdf = df[df['measure_id']==measure.id].copy()
        print(mdf[['measure_name', 'measure_id', 'unit', 'decimals', 'sensitive', 'value', 'value_new', 'value_org', 'spatialdimension_id', 'temporaldimension_id' ]])

        if hasattr(measure,"filter"):        
            raw_query =  f"select (public.apply_filter ({measure.id}, '{measure.filter.rule}', Null )).*" #{measure.filter.value_new}
            print(raw_query)

            with connection.cursor() as cursor:
                cursor.execute(raw_query)
                measure_obs = cursor.fetchall()

            def _transform_results_to_df(results: list) -> pd.DataFrame:
                """ Transform the query results into a pandas Dataframe
                :param results: dataframe returned from query"""

                # Create DataFrame
                _df = pd.DataFrame(results, columns=['created_at', 'update_at', 'id', 'value', 'measure_id', 'spatialdimension_id', 'temporaldimension_id'])
                # drop colums
                _df.drop(['created_at', 'update_at', 'id'], axis=1, inplace=True)

                return _df

            index = ['measure_id', 'spatialdimension_id', 'temporaldimension_id']
            dfobs = _transform_results_to_df(measure_obs)
            print(dfobs)

            # update mdf with new values
            mdf=mdf.merge(dfobs,
                    on=index,
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

        # save measure df in Publishobservation
        # set np.nan to None for postgres db -> OR TODO remove nan values from mdf because not necessary
        mdf['value'] = mdf['value'].replace(np.nan, None)
        PublicationObservation.objects.bulk_create(
            [   PublicationObservation( spatialdimensiontype=row["spatialdimensiontype"],
                                    spatialdimensiondate=row["spatialdimensiondate"], 
                                    spatialdimensioncode=row["spatialdimensioncode"],
                                    spatialdimensionname=row["spatialdimensionname"],
                                    temporaldimensiontype=row["temporaldimensiontype"],
                                    temporaldimensionstartdate=row["temporaldimensionstartdate"],
                                    temporaldimensionenddate=row["temporaldimensionenddate"],
                                    temporaldimensionyear=row["temporaldimensionyear"],
                                    measure=row["measure_name"],
                                    value=row["value"],
                                    ) for _, row in mdf.iterrows()
            ])

    try:
        return (f"All records for publish-observation are imported", messages.SUCCESS)

    except:
        print(f'------------{measure} niet aanwezig in data')
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR) 

    
