from django.contrib import admin, messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.db import connection

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
)


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


def publish_function(model):
    """
    runs the table function for publication:
    truncate table first and than runs function/query
    """

    truncate = f""" TRUNCATE TABLE {model._meta.db_table} RESTART IDENTITY; """

    match model._meta.model_name:
        case "publicationmeasure":
            raw_query = truncate + """ select public.publicatie_tabellen_publish_measures();"""

        case "publicationstatstics":
            raw_query = truncate + """ select  public.publicatie_tabellen_publish_statistics();"""

    try:
        print(raw_query)
        with connection.cursor() as cursor:
            cursor.execute(raw_query, {})
        result = (f"All records for {model._meta.model_name} are imported", messages.SUCCESS)
    except:
        # error
        result = (f"something went wrong", messages.ERROR)
    
    return result
        