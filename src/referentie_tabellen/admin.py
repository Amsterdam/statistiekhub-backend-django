from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from referentie_tabellen.models import (
    SpatialDimensionType,
    TemporalDimensionType,
    Theme,
    Unit,
)

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custum UsterAdmin"""

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()

        if not is_superuser:
            disabled_fields |= {
                "is_superuser",
                "user_permissions",
            }

        # Prevent non-superusers from editing their own permissions
        if not is_superuser and obj == request.user:
            disabled_fields |= {
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


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
    list_display = ("name", "id", "parent", "group")
    ordering = ("group", "id")


@admin.register(SpatialDimensionType)
class SpatialDimensionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "id")
    list_filter = ("source",)
    ordering = ("id",)
