from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from referentie_tabellen.models import (
    Source,
    SpatialDimensionType,
    TemporalDimensionType,
    Theme,
    Unit,
)

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom UserAdmin"""

    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("groups",)}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser:
            return self.fieldsets
        return super().get_fieldsets(request, obj)


# referentie tabellen
@admin.register(TemporalDimensionType)
class TemporalDimensionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "id")
    ordering = ("id",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "symbol", "id")
    ordering = ("id",)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "parent", "group")
    ordering = ("group__name", "name")


@admin.register(SpatialDimensionType)
class SpatialDimensionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "id")
    list_filter = ("source",)
    ordering = ("id",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "name_long", "id")
    list_filter = ("name",)
    ordering = ("name_long",)
