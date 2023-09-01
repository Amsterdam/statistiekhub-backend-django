from django.contrib import admin
from import_export.admin import ImportExportMixin

from statistiek_hub.resources.observation_resource import ObservationResource
from statistiek_hub.utils.formatters import SCSV


class ObservationAdmin(ImportExportMixin, admin.ModelAdmin):
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

    resource_classes = [ObservationResource]

    # change_list_template = "core/admin/change_list.html"

    def get_import_formats(self):
        """
        Returns available import formats.
        """

        return [SCSV]
