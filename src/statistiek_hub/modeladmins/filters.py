from django.contrib.admin import SimpleListFilter

from referentie_tabellen.models import TemporalDimensionType, Theme, SpatialDimensionType


class MeasureThemeFilter(SimpleListFilter):
    title = "measure theme"
    parameter_name = "theme"

    def lookups(self, request, model_admin):
        return Theme.objects.values_list("id", "name").order_by("name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(measure__theme_id=self.value())
        return queryset

class TemporalTypeFilter(SimpleListFilter):
    title = "temporal dimension type"
    parameter_name = "temporal_type"

    def lookups(self, request, model_admin):
        return TemporalDimensionType.objects.values_list("id", "name").order_by("name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(temporaldimension__type_id=self.value())
        return queryset

class SpatialTypeFilter(SimpleListFilter):
    title = "spatial dimension type"
    parameter_name = "spatial_type"

    def lookups(self, request, queryset):
        return SpatialDimensionType.objects.values_list("id", "name").order_by("name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(spatialdimension__type_id=self.value())
        return queryset
