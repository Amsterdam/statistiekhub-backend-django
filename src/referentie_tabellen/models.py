from django.db import models


class Unit(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=30, default="aantal")
    code = models.CharField(max_length=5, blank=True, null=True)
    symbol = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class Theme(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    name_uk = models.CharField(unique=True, max_length=50)
    abbreviation = models.CharField(unique=True, max_length=5)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class SpatialDimensionType(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(blank=True, null=True, max_length=100)

    def __str__(self):
        return f"{self.name}"


class TemporalDimensionType(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return f"{self.name}"

