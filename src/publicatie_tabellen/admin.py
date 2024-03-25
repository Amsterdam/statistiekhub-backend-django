from django.contrib import admin, messages
from django.db import connection
from django.db.models import F
from django.http import HttpResponseRedirect
from django.urls import path

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
)
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.truncate_model import truncate


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
        get_message, state = publish_function(self.model)
        self.message_user(request, get_message, state)
        return HttpResponseRedirect("../")


@admin.register(PublicationMeasure)
class PublicationMeasureTypeAdmin(NoAddDeleteChangePermission):
    list_display = ("name", "label", "id")
    ordering = ("id",)


@admin.register(PublicationObservation)
class PublicationObservationAdmin(NoAddDeleteChangePermission):
    list_display = ("id",)
    ordering = ("id",)


@admin.register(PublicationStatistic)
class PublicationStatisticAdmin(NoAddDeleteChangePermission):
    list_display = ("id",)
    ordering = ("id",)


def copy_queryset(queryset, copy_to_model):
    """ copy queryset into the copy_to_model"""
    new_item_list = []

    for item_obj in queryset:
        new_item_list.append(item_obj)

    copy_to_model.objects.bulk_create(new_item_list)  


def publish_function(model):
    """
    runs the table function for publication:
    truncate table first and than runs function/query
    """

    match model._meta.model_name:
        case "publicationmeasure":
            queryset = Measure.objects.select_related().all()\
                .defer("created_at", "updated_at", "owner_id", "id")\
                .annotate(theme_uk=F('theme__name_uk'), 
                          unit_code=F('unit__code'), 
                          unit_symbol=F('unit__symbol')
                          )

            try:
                truncate(PublicationMeasure)
                copy_queryset(queryset, PublicationMeasure)
                return (f"All records for {model._meta.model_name} are imported", messages.SUCCESS)
            except: # error
                return (f"something went wrong; WARNING table is not updated!", messages.ERROR)


        case "publicationstatistic":
            truncate(PublicationStatistic)
            raw_query =  """ select  public.publicatie_tabellen_publish_statistics();"""


        case "publicationobservation":
            measure_list = Measure.objects.filter(unit__name__in=["percentage",]).values_list('name', flat=True)
            print(measure_list)
            query = ""
            for measure in ["BEVTOTAAL"]: #measure_list:
                query += f""" select  public.publicatie_tabellen_publish_observations({measure});"""
            print(query)

            raw_query = query

    try:
        print(raw_query)
        with connection.cursor() as cursor:
            cursor.execute(raw_query, {})
        result = (f"All records for {model._meta.model_name} are imported", messages.SUCCESS)
    except:
        # error
        result = (f"something went wrong", messages.ERROR)

    return result
        

      