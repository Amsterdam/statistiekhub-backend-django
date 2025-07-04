from django.contrib import admin

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
    PublicationUpdatedAt,
)
from statistiek_hub.modeladmins.admin_mixins import GenericDateFilter


class NoAddDeleteChangePermission(admin.ModelAdmin):
    change_list_template = "publicatie_tabellen/changelist.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if instance := PublicationUpdatedAt.objects.first():
            updated_at = instance.updated_at
            extra_context['updated_at'] = updated_at.strftime("%d %B %Y, %I:%M %p")
        
        return super().changelist_view(request, extra_context=extra_context)


    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


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
    search_help_text = "search on measure name"
    search_fields = ["name"]


class SpatialdimensionDateFilter(GenericDateFilter):
    title = "spatialdimensiondate"
    parameter_name = "spatialdimensiondate"
    filter_field = "spatialdimensiondate"


@admin.register(PublicationObservation)
class PublicationObservationAdmin(NoAddDeleteChangePermission):
    search_fields = ["measure"]
    search_help_text = "search on measure name"

    def changelist_view(self, request, extra_context=None):
        # Controleer of er een zoekterm is
        search_term = request.GET.get('q')
        if not search_term:
            # Voeg een melding toe aan de context
            extra_context = extra_context or {}
            extra_context['show_message'] = True
        return super().changelist_view(request, extra_context=extra_context) 

    def get_queryset(self, request):
            # Controleer of er een zoekterm is opgegeven
            search_term = request.GET.get('q')  # 'q' is de parameter die door het search field wordt gebruikt
            if search_term:
                # Als er een zoekterm is, gebruik de standaard queryset
                return super().get_queryset(request)
            else:
                # Anders retourneer een lege queryset
                return self.model.objects.none()

    list_display = (
        "measure",
        "value",
        "temporaldimensiontype",
        "temporaldimensionyear",
        "spatialdimensiontype",
        "spatialdimensioncode",
        "spatialdimensiondate",
    )

    list_filter = (
        "temporaldimensiontype",
        "temporaldimensionyear",
        "spatialdimensiontype",
        SpatialdimensionDateFilter,
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
    search_help_text = "search on measure name"
    search_fields = ["measure"]
