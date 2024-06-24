import logging

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db.models.query import QuerySet
from django.db.models import F

from publicatie_tabellen.models import PublicationStatistic

from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_obs_publishstatistic(obsmodel) -> QuerySet:
    """ get queryset from obsmodel specificly for publishstatistic"""
    obs = obsmodel.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
                .filter(spatialdimension__type__name__in = ['Wijk','GGW-gebied', 'Gemeente'],
                        temporaldimension__type__name = 'Peildatum')\
                .exclude(measure__extra_attr__BBGA_kleurenpalet__in = [9,4] )\
                .annotate(spatialdimensiondate = F('spatialdimension__source_date'), 
                        spatialdimensioncode = F('spatialdimension__code'),
                        spatialdimensiontypename = F('spatialdimension__type__name'),
                        temporaldimensiontype = F('temporaldimension__type__name'),  
                        temporaldimensionstartdate = F('temporaldimension__startdate'),
                        temporaldimensionyear = F('temporaldimension__year'),
                        sd_minimum_bevtotaal = F('measure__extra_attr__BBGA_sd_minimum_bev_totaal'),
                        sd_minimum_wvoorbag = F('measure__extra_attr__BBGA_sd_minimum_wvoor_bag'),
                        measure_name = F('measure__name')
                        )\
                    .order_by('measure', 'temporaldimensionyear','temporaldimensionstartdate')\
                    .defer("created_at", "updated_at")\
                    .distinct()
    return obs


def publishstatistic() -> tuple:
    """select observations and calculate statistic
    exclude measures with:
    -kleurenpalet 9: geen kleuren /absolute aantallen; 
    -kleurenpalet 4: wit"
    return: tuple(string, django.contrib.messages)
    """

    qsobservation = _get_qs_obs_publishstatistic(Observation)
    qscalcobs = _get_qs_obs_publishstatistic(ObservationCalculated)
    print('-----------qscalcobs', qscalcobs)
    print('--- qsobservation', len(qsobservation))

    if not (qsobservation or qscalcobs):
        return (f"There are no observations standarddeviation could be applied to", messages.ERROR)

    #-- set queryset observations into dataframe # qsobservation._fields
    df_obs = pd.DataFrame(list(qsobservation.values()), columns=qsobservation._fields)
    df_calc =pd.DataFrame(list(qscalcobs.values()), columns=qscalcobs._fields)
    print('------------- df obs', df_obs.head())
    print('------------- df calc', df_calc.head())
    df = pd.concat([df_obs, df_calc], ignore_index=True)

    # qsmin = bevtotaal + wvoorrbag voor wijk en ggw-gebied
    qsmin = Observation.objects.select_related('measure', 'spatialdimension', 'temporaldimension')\
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

    dfmin = pd.DataFrame(list(qsmin.values()), columns=qsmin._fields)

    print('-----------------------------------------------------')
    print('aanmaken df met gemiddelde')
    #gemiddelde van de var_p is het stadsgegeven
    df_mean = df[df['spatialdimensioncode'] == '0363']\
                        [[ "spatialdimensiondate", 
                            "temporaldimensiontype", 
                            "temporaldimensionstartdate",
                            "temporaldimensionyear", 
                            "measure_id", "measure_name", "value",]]\
                        .rename(columns={'value':'average'}).dropna(subset=['average'])

    #TODO wat te doen met variabelen die geen std hebben omdat geen wijk en/of 22 gebied?
    
    df_wijk_ggw = df[df['spatialdimensiontypename'].isin(['Wijk','GGW-gebied'])]\
                        [[ "spatialdimensiondate",
                            "spatialdimensiontypename", 
                            "spatialdimensioncode", 
                            "temporaldimensiontype", 
                            "temporaldimensionstartdate",
                            "temporaldimensionyear",
                            "sd_minimum_bevtotaal",
                            "sd_minimum_wvoorbag",
                            "measure_id", "measure_name", "value",]]
                    
    print('remove value observation if sd_minimum_bevtotaal or sd_minimum_wvoorbag condition is not met')

    def sd_minimum_check(var, var_check, sd_var):
        print('-----var check', var_check)

        # get the values of bevtotaal or wvoorrbag
        _bbga_var_check= dfmin[(dfmin['measure_name'] == var)][["temporaldimensionyear", "spatialdimensiondate", "spatialdimensioncode", "value"]] 
    
        _hulp = sd_var.join(_bbga_var_check.rename(columns={"value": 'varc'})\
                            .set_index(["temporaldimensionyear", "spatialdimensiondate", "spatialdimensioncode"]),\
                                    on=["temporaldimensionyear", "spatialdimensiondate", "spatialdimensioncode"], how='left')\
                                    .replace({None: np.nan})
        #'value' vervangen door onbekend als te klein
        _hulp.loc[(_hulp['varc'] < _hulp[var_check]), "value"] = np.nan

        return _hulp.drop('varc', axis=1)

    _hulp  = sd_minimum_check('BEVTOTAAL', 'sd_minimum_bevtotaal', df_wijk_ggw)
    _hulp2 = sd_minimum_check('WVOORRBAG', 'sd_minimum_wvoorbag', _hulp)

    df_wijk_ggw = _hulp2

    def sd_berekening(_hulptwee):
        df = _hulptwee.dropna(subset=['value']).copy()
        #door het format per variabele kan de std niet berekend worden -> daarom eerst value omzetten naar float
        df['value'] = df['value'].astype(float)       
        print(df.head())

        # splitsing in wijk en gebied22
        df_wijk = df[df['spatialdimensiontypename'] == 'Wijk'].groupby(['temporaldimensionyear',"measure_id"]).agg({'value': 'std'}).rename(columns={'value': 'sd_wijk'}).reset_index()
        df_wijk["bron_wijk"] = 'sdbc'
        df_geb = df[df['spatialdimensiontypename'] == 'GGW-gebied'].groupby(['temporaldimensionyear',"measure_id"]).agg({'value': 'std'}).rename(columns={'value': 'sd_geb'}).reset_index()
        df_geb["bron_geb"] = 'sdgeb22'

        # sd wijk en geb22 samenvoegen
        df1 = df_wijk.join(df_geb.set_index(['temporaldimensionyear', "measure_id"]), on=['temporaldimensionyear', "measure_id"], how ='outer')   
        df1.reset_index(inplace=True)    
        
        # als sd wijk bestaat die nemen anders pas geb22
        df1['standarddeviation'] = df1['sd_wijk'].combine_first(df1['sd_geb'])
        # noteren waar de sd vandaan komt als source
        df1["source"] = df1["bron_wijk"].combine_first(df1["bron_geb"])

        # df1.loc[df1['standarddeviation'] == df1['sd_wijk'], 'source'] = 'sdbc'
        # df1.loc[df1['standarddeviation'] == df1['sd_geb'], 'source'] = 'sdgeb22'    
    
        return df1[["temporaldimensionyear","measure_id","standarddeviation","source"]]
    
    # berekening sd op wijk en geb22
    print('berekenen sd')
    _hulp3 = sd_berekening(_hulp2)

    dfstatistic = df_mean.join(_hulp3.set_index(["temporaldimensionyear","measure_id"]), on=["temporaldimensionyear", "measure_id"], how='left').replace({np.nan: None})
    measure_no_sd = dfstatistic[dfstatistic['standarddeviation'].isna()]['measure_name'].values
    # if there is no standarddeviation -> remove record
    dfstatistic.dropna(subset=['standarddeviation'], inplace=True)

    # gemiddelde en std afronden op 3 decimalen -> set on the model field
    
    try:
        truncate(PublicationStatistic)
        PublicationStatistic.objects.bulk_create(
            [   PublicationStatistic(spatialdimensiondate=row["spatialdimensiondate"], 
                                        temporaldimensiontype=row["temporaldimensiontype"],
                                        temporaldimensionstartdate=row["temporaldimensionstartdate"],
                                        temporaldimensionyear=row["temporaldimensionyear"],
                                        measure=row["measure_name"],
                                        average=row["average"],
                                        standarddeviation=row["standarddeviation"],
                                        source=row["source"]
                                        ) for _, row in dfstatistic.iterrows()
            ])
        return (f"All records for publish-statistic are imported, WARNING Not included: no standarddeviation for {measure_no_sd}", messages.SUCCESS)
    except: # error
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR)
