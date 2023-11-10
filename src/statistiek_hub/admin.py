from django.contrib import admin

from .modeladmins.filter_admin import FilterAdmin
from .modeladmins.measure_admin import MeasureAdmin
from .modeladmins.observation_admin import ObservationAdmin
from .modeladmins.spatial_dimension_admin import SpatialDimensionAdmin
from .modeladmins.temporal_dimension_admin import TemporalDimensionAdmin
from .models.dimension import Dimension
from .models.dimension_group import DimensionGroup
from .models.filter import Filter
from .models.measure import Measure
from .models.observation import Observation
from .models.spatial_dimension import SpatialDimension
from .models.temporal_dimension import TemporalDimension
from .models.topic import Topic
from .models.topic_set import TopicSet

# Register your models here.


# uitgebreide Admin functionaliteiten - import/export, leaflet, validatiechecks etc.
admin.site.register(Measure, MeasureAdmin)
admin.site.register(Observation, ObservationAdmin)
admin.site.register(SpatialDimension, SpatialDimensionAdmin)
admin.site.register(TemporalDimension, TemporalDimensionAdmin)

admin.site.register(Filter, FilterAdmin)


# display admin
@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "id")
    list_filter = ("dimensiongroup__dimensionkey", "dimensiongroup__name")
    ordering = ("id",)


@admin.register(DimensionGroup)
class DimensionGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "dimensionkey", "id")
    ordering = ("id",)


@admin.register(TopicSet)
class TopicSetAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "measure")
    list_filter = ("topic",)
    ordering = ("id",)
    search_help_text = "search on measure name"
    search_fields = ["measure__name"]


admin.site.register(Topic)
