from django.contrib import admin
from django.http.request import HttpRequest

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
)


class NoAddDeleteChangePermission(admin.ModelAdmin):

    def has_add_permission(self, request) -> bool:
        return False

    #def has_delete_permission(self, request, obj=None) -> bool:
        return False
    
    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(PublicationMeasure)
class PublicationMeasureTypeAdmin(NoAddDeleteChangePermission):
    list_display = ("name", "id")
    ordering = ("id",)


@admin.register(PublicationObservation)
class PublicationObservationAdmin(NoAddDeleteChangePermission):
    list_display = ("id",)
    ordering = ("id",)


@admin.register(PublicationStatistic)
class PublicationStatisticAdmin(NoAddDeleteChangePermission):
    list_display = ("id",)
    ordering = ("id",)

