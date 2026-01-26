from django.contrib import admin, messages
from import_export.tmp_storages import MediaStorage

from statistiek_hub.modeladmins.admin_mixins import (
    CheckPermissionUserMixin,
    ImportExportFormatsMixin,
)
from statistiek_hub.modeladmins.filters import (
    MeasureThemeFilter,
    SpatialTypeFilter,
    TemporalTypeFilter,
)
from statistiek_hub.modeladmins.pagination import LimitedPaginator, PageLimitExceeded
from statistiek_hub.models.observation import ObservationCalculated
from statistiek_hub.resources.observation_resource import ObservationResource


class ObservationAdmin(
    ImportExportFormatsMixin, CheckPermissionUserMixin, admin.ModelAdmin
):
    tmp_storage_class = MediaStorage

    search_help_text = "search on measure name"
    search_fields = ["measure__name"]

    list_per_page = 100
    paginator = LimitedPaginator
    pagination_max_offset = 250_000

    list_display = (
        "id",
        "measure",
        "value",
        "temporaldimension",
        "spatialdimension",
        "created_at",
        "updated_at",
    )

    list_filter = (
        MeasureThemeFilter,
        TemporalTypeFilter,
        SpatialTypeFilter,
    )
    show_facets = admin.ShowFacets.NEVER

    raw_id_fields = (
        "measure",
        "temporaldimension",
        "spatialdimension",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["measure", "temporaldimension", "spatialdimension"]
        return []

    resource_classes = [ObservationResource]

    def get_paginator(
        self, request, queryset, per_page, orphans=0, allow_empty_first_page=True
    ):
        return self.paginator(
            queryset,
            per_page,
            orphans=orphans,
            allow_empty_first_page=allow_empty_first_page,
            max_offset=self.pagination_max_offset,
        )

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except PageLimitExceeded as e:
            messages.error(
                request,
                f"Page {e.requested_page} is not available (maximum page allowed: {e.max_pages}). "
                f"Please use search or filters to find specific records.",
            )

            from django.http import HttpResponseRedirect

            query_params = request.GET.copy()
            query_params["p"] = e.max_pages
            return HttpResponseRedirect(f"{request.path}?{query_params.urlencode()}")

    def get_search_results(self, request, queryset, search_term):
        """
        Override to use subquery approach for better performance
        """
        if not search_term:
            return queryset, False

        # Avoid circular imports
        from statistiek_hub.models.measure import Measure

        # Gets run as a subquery
        matching_measure_id_qs = Measure.objects.filter(
            name__icontains=search_term
        ).values_list("id", flat=True)

        # Filter observations by these measure IDs
        queryset = queryset.filter(measure_id__in=matching_measure_id_qs)

        return queryset, False

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.resolver_match.url_name.endswith("_changelist"):
            return qs.only(
                "id",
                "value",
                "created_at",
                "updated_at",
                "measure_id",
                "temporaldimension_id",
                "spatialdimension_id",
                "measure__name",
                "temporaldimension__name",
                "spatialdimension__name",
                "spatialdimension__source_date",
            ).select_related(
                "measure",
                "temporaldimension",
                "spatialdimension",
            )
        else:
            return qs.select_related(
                "measure",
                "temporaldimension",
                "spatialdimension",
            )


@admin.register(ObservationCalculated)
class ObservationCalculatedAdmin(admin.ModelAdmin):
    tmp_storage_class = MediaStorage
    list_display = (
        "id",
        "measure",
        "value",
        "temporaldimension",
        "spatialdimension",
        "created_at",
        "updated_at",
    )

    list_filter = (
        ("temporaldimension__type", admin.RelatedOnlyFieldListFilter),
        ("spatialdimension__type", admin.RelatedOnlyFieldListFilter),
    )
    search_help_text = "search on measure name"
    search_fields = ["measure__name"]
    ordering = ("measure",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
