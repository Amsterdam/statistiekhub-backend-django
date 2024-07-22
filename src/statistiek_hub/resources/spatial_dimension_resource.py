from django.contrib.gis.geos import GEOSGeometry
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from referentie_tabellen.models import SpatialDimensionType
from statistiek_hub.models.spatial_dimension import SpatialDimension


class SpatialDimensionResource(ModelResource):
    type = Field(
        column_name="type",
        attribute="type",
        widget=ForeignKeyWidget(SpatialDimensionType, field="name"),
    )

    def before_import_row(self, row, **kwargs):
        if row["geom"] == "":
            row["geom"] = None
        else:
            row["geom"] = GEOSGeometry(row["geom"], srid=28992)

    class Meta:
        model = SpatialDimension
        exclude = ("id",)
        import_id_fields = ("code", "type", "source_date")
