from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
    PublicationUpdatedAt,
)
from publicatie_tabellen.publication_main import PublishFunction


class NoAddDeleteChangePermission(admin.ModelAdmin):
    change_list_template = "publicatie_tabellen/changelist.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if instance :=PublicationUpdatedAt.objects.first():
            updated_at = instance.updated_at
            extra_context['updated_at'] = updated_at.strftime("%d %B %Y, %I:%M %p")
        
        return super().changelist_view(request, extra_context=extra_context)


    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("publish/", self.publish),
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
        "temporaldimensionyear",
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
    list_display = (
        "id",
        "measure",
        "temporaldimensionyear",
        "spatialdimensiondate",
        "average",
        "standarddeviation",
        "source",
    )
    ordering = ("id",)
