from django.contrib import messages
from django.db import connection

from django.db.models.query import QuerySet
from django.db.models import F, StdDev, Q, Value, Count, Subquery
from django.db.models.functions import Round
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.models.filter import Filter

from statistiek_hub.utils.truncate_model import truncate
import re
import pandas as pd
import numpy as np

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
)

class PublishFunction:
    def __init__(self, model) -> None:
        self.model = model
        self.result = None

        self.publish_function()

    def publish_function(self):
        """
        runs the correct model-function for publication:
        truncate table first and than runs function/query
        """
        print(self.model._meta.model_name)

        match self.model._meta.model_name:
            case "publicationmeasure":
                self.publishmeasure()

            case "publicationstatistic":
                self.publishstatistic()
                print(self.result)

            case "publicationobservation":
                self.fill_observationcalculated()
                self.publishobservation()
                print(self.result)


    def fill_observationcalculated(self):

        # get calculation measures -> select from observations otherwise they can not exist
        qsmeasurecalc = Measure.objects.exclude(calculation = '')
        print('----------lengte-qsmeasurecalc:', len(qsmeasurecalc))

        truncate(ObservationCalculated)
        for measure in qsmeasurecalc:
            print('---measure', measure)
            raw_query =  f"select (public.calculate_observation ({measure.id}, '{measure.calculation}')).*"
            print(raw_query)

            with connection.cursor() as cursor:
                cursor.execute(raw_query)
                measure_calcobs = cursor.fetchall()
            print( measure_calcobs )

            def _transform_results(results: list) -> list:
                """
                Transform the query results into
                list of ObservationCalculated objects
                :param results: list of tuples returned from query"""

                new_item_list = []
                for row in results:
                    new_item_list.append( ObservationCalculated(measure_id=row[4],
                                          value= row[3],
                                          spatialdimension_id = row[5],
                                          temporaldimension_id = row[6],
                                          ))
                return new_item_list

            ObservationCalculated.objects.bulk_create(_transform_results(measure_calcobs)) 

            #result = (f"All records for calculated observations are imported", messages.SUCCESS)
            # except:
            #     # error
            #     result = (f"something went wrong", messages.ERROR)

        # print('------------result', result)


    @staticmethod
    def _copy_queryset(queryset, copy_to_model):
        """ copy queryset into the copy_to_model"""
        new_item_list = []

        for item_obj in queryset:
            new_item_list.append(item_obj)

        copy_to_model.objects.bulk_create(new_item_list)      


    def publishmeasure(self):
        queryset = Measure.objects.select_related("theme", "unit").all()\
                    .defer("created_at", "updated_at", "owner_id", "id")\
                    .annotate(theme_uk=F('theme__name_uk'), 
                            unit_code=F('unit__code'), 
                            unit_symbol=F('unit__symbol')
                            )
        try:
            truncate(PublicationMeasure)
            self._copy_queryset(queryset, PublicationMeasure)
            self.result = (f"All records for {self.model._meta.model_name} are imported", messages.SUCCESS)
        except: # error
            self.result = (f"something went wrong; WARNING table is not updated!", messages.ERROR)

    @staticmethod
    def _round_to_base(x, base=5):
        return base * round(x/base)

    @staticmethod
    def _split_filter_rules(msfilter) -> list:
        # possibility of multiple filter-rules, decompose start on '(' and end on')'
        rule = re.split(r'\((.+?)\)', msfilter['rule'])
        return [ x.strip() for x in rule if x] #remove spaces
    
    @staticmethod
    def _split_rule(rule) -> list:
        # decompose one rule on spaces
        return re.split('\s+', rule)

    def _apply_sensitive_rules(self, observation) -> float:
        value = observation.value_org
        match observation.unit:
            case 'aantal':
                # afronden op 5 tallen
                if 0 < value < 5:
                    return 5
                else:
                    return self._round_to_base(value, 5)

            case 'percentage':
                # afronden naar 90%
                if value >= 90:
                    return 90
        # else
        return observation.value_new

    def _get_qs_obs_publishobservation(self, obsmodel) -> QuerySet:
        """ get queryset from obsmodel specificly for publishobservations"""
        # select observations
        obs = Observation.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
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
                            value_new = Round('value', precision='measure__decimals')
                            ).defer("created_at", "updated_at")
        return obs

    def publishobservation(self):
        "select observations and change value"


        # select observations
        qsobservation = self._get_qs_obs_publishobservation(Observation)
        self.fill_observationcalculated()
        qscalcobs = self._get_qs_obs_publishobservation(ObservationCalculated)
        print('-----------qscalcobs', qscalcobs)

        #-- set queryset observations into dataframe # qsobservation._fields
        df_obs = pd.DataFrame(list(qsobservation.values()), columns=qsobservation._fields)
        df_calc =pd.DataFrame(list(qscalcobs.values()), columns=qscalcobs._fields)
        print('------------- df obs', df_obs.head())
        print('------------- df calc', df_calc.head())
        df = pd.concat([df_obs, df_calc], ignore_index=True)

        # select filters
        qsfilter = Filter.objects.all().values()

        new_item_list = []       
        for obj in qsobservation:
            # set value on rounded value
            obj.value = obj.value_new

            # check if sensitive and apply privacy rules
            if obj.sensitive:
                obj.value = self._apply_sensitive_rules(obj)

            # check if filter needs to be applied
            if msfilter := qsfilter.filter(measure = obj.measure):
                #print('-----msfilter', msfilter)
                
                # possibility of multiple filter-rules
                value = obj.value
                for msf in msfilter:
                    rules = self._split_filter_rules(msf)
                    #print(rules)
                    for clr in rules:
                        #print('clr:', clr) 
                        clr_part = self._split_rule(clr)
                        #print('clr_part: ',clr_part)
                        if clr_part[0].startswith('$'):
                            # select basemeasure value
                            basems_value = qsobservation.filter(measure__name=clr_part[0][1:], 
                                                    spatialdimension = obj.spatialdimension, 
                                                    temporaldimensionyear = obj.temporaldimensionyear).values('value_org')
                        
                            if eval(f"{basems_value[0]['value_org']}{clr_part[1]}{clr_part[2]}"):
                                # apply filter
                                value = msf['value_new']
                                
                obj.value = value
                #TODO: checken of het goed gaat met OR en AND en meerdere regels

            new_item_list.append(obj)

        try:
            truncate(PublicationObservation)
            PublicationObservation.objects.bulk_create(new_item_list) 
            self.result = (f"All records for {self.model._meta.model_name} are imported", messages.SUCCESS)
        except: # error
            self.result = (f"something went wrong; WARNING table is not updated!", messages.ERROR)        

    def _get_qs_obs_publishstatistic(self, obsmodel) -> QuerySet:
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


    def publishstatistic(self):
        """select observations and calculate statistic
        exclude #kleurenpalet 9: geen kleuren /absolute aantallen; kleurenpalet 4: wit"
        """

        qsobservation = self._get_qs_obs_publishstatistic(Observation)
        qscalcobs = self._get_qs_obs_publishstatistic(ObservationCalculated)
        print('-----------qscalcobs', qscalcobs)
        if not qscalcobs:
            print('ObservationCalculated is not yet filled')
            self.fill_observationcalculated()
            qscalcobs = self._get_qs_obs_publishstatistic(ObservationCalculated)
        print('-----------qscalcobs', qscalcobs)   
        print('--- qsobservation', len(qsobservation))

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
            self.result = (f"All records for {self.model._meta.model_name} are imported, WARNING Not included: no standarddeviation for {measure_no_sd}", messages.SUCCESS)
        except: # error
            self.result = (f"something went wrong; WARNING table is not updated!", messages.ERROR)
