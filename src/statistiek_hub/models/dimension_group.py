from django.db import models


class DimensionGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    dimensionkey = models.CharField(max_length=50)
    name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=15)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.dimensionkey}:{self.name}"

    class Meta:
        managed = True
        db_table = "dimensiongroup"
