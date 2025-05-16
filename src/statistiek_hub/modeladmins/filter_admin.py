from django.contrib import admin
from django.http import HttpRequest
from import_export.admin import ImportMixin

from statistiek_hub.resources.filter_resource import FilterResource

from .admin_mixins import CheckPermissionUserMixin, ImportExportFormatsMixin


class FilterAdmin(ImportExportFormatsMixin, CheckPermissionUserMixin, admin.ModelAdmin):
    list_display = (
        "measure",
        "rule",
        "value_new",
    )
    ordering = ("measure",)
    raw_id_fields = ("measure",)
    resource_classes = [FilterResource]
