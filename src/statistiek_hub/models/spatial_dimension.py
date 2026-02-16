from django.contrib.gis.db.models import GeometryField
from django.db import models

from referentie_tabellen.models import SpatialDimensionType


class SpatialDimension(models.Model):
    class Meta:
        indexes = [
            models.Index("code", "type", "source_date", name="unique_spatialdimension_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                name="duplicate_specdim_constraint",
                fields=["code", "type", "source_date"],
            )
        ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=100)
    type = models.ForeignKey(SpatialDimensionType, on_delete=models.RESTRICT)
    source_id = models.CharField(max_length=100, blank=True, null=True)
    source_date = models.DateField()
    geom = GeometryField(srid=28992, blank=True, null=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.source_date}"
