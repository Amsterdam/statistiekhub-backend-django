from django.db import models

from .dimension_group import DimensionGroup


class Dimension(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    code = models.CharField(unique=True, max_length=10)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=15)
    dimensiongroup = models.ForeignKey(DimensionGroup, on_delete=models.RESTRICT)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "dimension"
