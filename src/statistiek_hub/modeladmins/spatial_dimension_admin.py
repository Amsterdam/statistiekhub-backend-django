from django.contrib import admin
from import_export.admin import ImportMixin
from leaflet.admin import LeafletGeoAdminMixin

from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.resources.spatial_dimension_resource import SpatialDimensionResource
from statistiek_hub.utils.formatters import GEOJSON


class SourceDateFilter(admin.SimpleListFilter):
    title = "source date"
    parameter_name = "source_date"

    def lookups(self, request, model_admin):
        """
        Choices to propose all years in spatial_dimension table
        """
        sdates = list(
            SpatialDimension.objects.order_by("source_date")
            .values_list("source_date", flat=True)
            .distinct()
        )
        listsdates = [(str(x), str(x)) for x in sdates]  # Declaration of the list

        return listsdates

    def queryset(self, request, queryset):
        if self.value():  # If a source_date is set, we filter else not
            return queryset.filter(source_date=self.value())
        else:
            return queryset


class SpatialDimensionAdmin(ImportMixin, LeafletGeoAdminMixin, admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "source_date",
        "type",
        "id",
    )
    list_filter = (("type", admin.RelatedOnlyFieldListFilter), SourceDateFilter)
    ordering = ("id",)
    modifiable = False  # Make the leaflet map read-only
    resource_class = SpatialDimensionResource

    def get_import_formats(self):
        """
        Returns GEOJSON import formats.
        """
        return [GEOJSON]

    # This will help you to disbale add functionality
    def has_add_permission(self, request):
        return False
