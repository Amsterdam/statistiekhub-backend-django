from django.contrib import admin
from import_export.admin import ImportMixin

from statistiek_hub.resources.filter_resource import FilterResource
from statistiek_hub.utils.formatters import SCSV


class FilterAdmin(ImportMixin, admin.ModelAdmin):
    list_display = (
        "measure",
        "rule",
        "value_new",
        "id",
    )
    ordering = ("measure",)
    resource_classes = [FilterResource]

    def get_import_formats(self):
        return [SCSV] + self.formats
