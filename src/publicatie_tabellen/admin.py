from django.contrib import admin, messages
from django.db import connection
from django.db.models import F, StdDev, Q
from django.db.models.functions import Round
from django.http import HttpResponseRedirect
from django.urls import path

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
)
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.models.filter import Filter
from statistiek_hub.utils.truncate_model import truncate
import re

import pandas as pd


class NoAddDeleteChangePermission(admin.ModelAdmin):
    change_list_template = "publicatie_tabellen/changelist.html"

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('publish/', self.publish),
        ]
        return my_urls + urls

    def publish(self, request):
        get_message, state = PublishFunction(model=self.model).result
        self.message_user(request, get_message, state)
        return HttpResponseRedirect("../")


@admin.register(PublicationMeasure)
class PublicationMeasureTypeAdmin(NoAddDeleteChangePermission):
    list_display = (
        "name",
        "label",
        "theme",
        "sensitive",
        "deprecated",
    )
    list_filter = (
        "theme",
        "unit",
        "sensitive",
        "deprecated",
    )


@admin.register(PublicationObservation)
class PublicationObservationAdmin(NoAddDeleteChangePermission):
    list_display = (
        "id",
        "measure",
        "value",
        "temporaldimensiontype",
        "spatialdimensiontype",
        "spatialdimensioncode",
    )

    list_filter = (
        "temporaldimensiontype",
        "temporaldimensionyear",
        "spatialdimensiontype",
        "spatialdimensiondate",
    )


@admin.register(PublicationStatistic)
class PublicationStatisticAdmin(NoAddDeleteChangePermission):
    list_display = ("id",)
    ordering = ("id",)



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
                #truncate(PublicationStatistic)
                #raw_query =  """ select  public.publicatie_tabellen_publish_statistics();"""
                self.publishstatistic()
                print(self.result)

            case "publicationobservation":
                self.publishobservation()
                print(self.result)

        # try:
        #     print(raw_query)
        #     with connection.cursor() as cursor:
        #         cursor.execute(raw_query, {})
        #     result = (f"All records for {self.model._meta.model_name} are imported", messages.SUCCESS)
        # except:
        #     # error
        #     result = (f"something went wrong", messages.ERROR)

        # return result

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

    def _apply_sensitive_rules(self, observation: Observation) -> float:
        match observation.unit:
            case 'aantal':
                # afronden op 5 tallen
                if 0 < observation.value_org < 5:
                    return 5
                else:
                    return self._round_to_base(observation.value_org, 5)

            case 'percentage':
                # afronden naar 90%
                if observation.value_org >= 90:
                    return 90

    def publishobservation(self):
        "select observations and change value"

        # select observations
        qsobservation = Observation.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
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
                            value_org= F('value'),
                            value_new = Round('value', precision='measure__decimals')
                            ).defer("created_at", "updated_at")
        
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
                print('measure gevonden in filter', msfilter )

                # possibility of multiple filter-rules
                value = obj.value
                for msf in msfilter:
                    rules = self._split_filter_rules(msf)
                    print(rules)
                    for clr in rules:
                        print('clr:', clr) 
                        clr_part = self._split_rule(clr)
                        print('clr_part: ',clr_part)
                        if clr_part[0].startswith('$'):
                            # select basemeasure value
                            basems_value = qsobservation.filter(measure__name=clr_part[0][1:], 
                                                    spatialdimension = obj.spatialdimension, 
                                                    temporaldimensionyear = obj.temporaldimensionyear).values('value_org')
                            
                            print('test: ', f"{obj.value_org} {clr_part[1]} {basems_value[0]['value_org']}")
                            if eval(f"{obj.value_org} {clr_part[1]} {basems_value[0]['value_org']}"):
                                # apply filter
                                print('voor',obj.value)
                                value = msf['value_new']
                                print('na',obj.value)

                obj.value = value
                #TODO: checken of het goed gaat met OR en AND en meerdere regels

            new_item_list.append(obj)

        try:
            truncate(PublicationObservation)
            PublicationObservation.objects.bulk_create(new_item_list) 
            self.result = (f"All records for {self.model._meta.model_name} are imported", messages.SUCCESS)
        except: # error
            self.result = (f"something went wrong; WARNING table is not updated!", messages.ERROR)        

    def publishstatistic(self):
        """select observations and calculate statistic
        exclude #kleurenpalet 9: geen kleuren /absolute aantallen; kleurenpalet 4: wit"
        """

        s_deviation = StdDev("value", filter=Q(measure=1))

        qsobservation = Observation.objects.select_related('measure', 'spatialdimension', 'temporaldimension', 'measure__unit', 'spatialdimension__type','temporaldimension__type').all()\
                    .filter(spatialdimension__type__name__in=['Wijk','GGW-gebied', 'Gemeente'])\
                    .exclude(measure__extra_attr__BBGA_kleurenpalet__in = [9,4] )\
                    .annotate(spatialdimensiondate=F('spatialdimension__source_date'), 
                            spatialdimensioncode=F('spatialdimension__code'), 
                            temporaldimensiontype=F('temporaldimension__type__name'),  
                            temporaldimensionstartdate=F('temporaldimension__startdate'),
                            temporaldimensionyear=F('temporaldimension__year'),
                            sd_minimum_bevtotaal = F('measure__extra_attr__BBGA_sd_minimum_bev_totaal'),
                            sd_minimum_wontotaal = F('measure__extra_attr__BBGA_sd_minimum_won_totaal'),
                            measure_naam = F('measure__name')
                            ).defer("created_at", "updated_at")

        qsbevtotaal = Observation.objects.filter(measure__name=['BEVTOTAAL'])
        qswvoorrbag = Observation.objects.filter(measure__name=['WVOORRBAG'])

        #TODO kijken of value_new gelijk gefilterd kan worden op sd_minimum.... in queryset scheelt data
        q_wijk = qsobservation.filter(spatialdimension__type__name = 'Gemeente')
        print(q_wijk)

        # average = models.FloatField()
        # standarddeviation = models.FloatField()
        # source = models.CharField(max_length=100)
        new_item_list = []       
        for obj in q_wijk:
            print(obj.__dict__)
            #print(obj.sd_minimum_bevtotaal['BBGA_sd_minimum_bev_totaal'])

            print(obj.sd_minimum_bevtotaal)
            print(obj.spatialdimension)
            print(obj.temporaldimensionyear)
            print(qsobservation.__dict__)
            if obj.sd_minimum_bevtotaal:
                #TODO hij selecteerd niet?????? er gaat iets mis misschien bevat qsobservation geen 'bevtotaal'?? 
                # select basemeasure value
                basems_value = qsobservation.filter( measure__name= 'BEVTOTAAL',
                                                   spatialdimension = obj.spatialdimension, 
                                                   temporaldimensionyear = obj.temporaldimensionyear)
                print('bevtotaal', basems_value)
                # apply


            obj.average = 1
            obj.standaarddeviation = 1
            obj.source = 1
            new_item_list.append(obj)  

        try:
            truncate(PublicationStatistic)
            PublicationStatistic.objects.bulk_create(new_item_list) 
            self.result = (f"All records for {self.model._meta.model_name} are imported", messages.SUCCESS)
        except: # error
            self.result = (f"something went wrong; WARNING table is not updated!", messages.ERROR)
