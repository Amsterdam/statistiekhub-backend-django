from django.contrib import admin

from publicatie_tabellen.models import (
    PublicationMeasure,
    PublicationObservation,
    PublicationStatistic,
    PublicationUpdatedAt,
)
from statistiek_hub.modeladmins.admin_mixins import DynamicListFilter


class NoAddDeleteChangePermission(admin.ModelAdmin):
    change_list_template = "publicatie_tabellen/changelist.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if instance := PublicationUpdatedAt.objects.first():
            updated_at = instance.updated_at
            extra_context["updated_at"] = updated_at.strftime("%d %B %Y, %I:%M %p")

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


class SpatialdimensionDateFilter(DynamicListFilter):
    title = "spatialdimensiondate"
    parameter_name = "spatialdimensiondate"
    filter_field = "spatialdimensiondate"


class TemporaldimensionYearFilter(DynamicListFilter):
    title = "temporaldimensionyear"
    parameter_name = "temporaldimensionyear"
    filter_field = "temporaldimensionyear"


class SpatialdimensionTypeFilter(DynamicListFilter):
    title = "spatialdimensiontype"
    parameter_name = "spatialdimensiontype"
    filter_field = "spatialdimensiontype"


@admin.register(PublicationObservation)
class PublicationObservationAdmin(NoAddDeleteChangePermission):
    list_per_page = 25  # Reduce the number of items per page
    search_fields = ["measure"]
    search_help_text = "search on measure name"

    def changelist_view(self, request, extra_context=None):
        # Controleer of er een zoekterm is
        search_term = request.GET.get("q")
        if not search_term:
            # Voeg een melding toe aan de context
            extra_context = extra_context or {}
            extra_context["show_message"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        search_term = request.GET.get("q")
        if search_term:
            escaped_search_term = search_term.replace("_", r"\_")
            return self.model.objects.filter(measure__icontains=escaped_search_term.upper())

        # include an object if being accessed so detailview works
        if request.resolver_match.kwargs.get("object_id"):
            object_id = request.resolver_match.kwargs["object_id"]
            return self.model.objects.filter(pk=object_id)
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
        TemporaldimensionYearFilter,
        SpatialdimensionTypeFilter,
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
