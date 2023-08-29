from django.contrib import admin
from referentie_tabellen.models import (SpatialDimensionType,
                                        TemporalDimensionType, Theme, Unit)


# referentie tabellen
@admin.register(TemporalDimensionType)
class TemporalDimensionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "id")
    ordering = ("id",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "symbol", "id")
    ordering = ("id",)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "id")
    ordering = ("id",)


@admin.register(SpatialDimensionType)
class SpatialDimensionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "id")
    list_filter = ("source",)
    ordering = ("id",)
