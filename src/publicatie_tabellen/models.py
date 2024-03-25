from django.db import models


class PublicationMeasure(models.Model):
    name = models.CharField(unique=True, max_length=50)
    label = models.CharField(max_length=75)
    label_uk = models.CharField(max_length=75, blank=True, null=True)
    definition = models.TextField()
    definition_uk = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=100)
    theme = models.CharField(max_length=50)
    theme_uk = models.CharField(max_length=50)
    unit = models.CharField(max_length=30)
    unit_code = models.CharField(max_length=5, blank=True, null=True)
    unit_symbol = models.CharField(max_length=15, blank=True, null=True)
    decimals = models.IntegerField()
    sensitive = models.BooleanField()
    parent = models.CharField(max_length=50, blank=True, null=True)
    extra_attr = models.JSONField(blank=True, null=True)
    deprecated = models.BooleanField()
    deprecated_date = models.DateField(blank=True, null=True)
    deprecated_reason = models.TextField(blank=True, null=True)
    calculation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class PublicationObservation(models.Model):
    spatialdimensiontype = models.CharField(max_length=50)
    spatialdimensiondate = models.DateField()
    spatialdimensioncode = models.CharField(max_length=100)
    spatialdimensionname = models.CharField(max_length=100, blank=True, null=True)
    temporaldimensiontype = models.CharField(max_length=50)
    temporaldimensionstartdate = models.DateField()
    temporaldimensionenddate = models.DateField()
    measure = models.CharField(max_length=50)
    value = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class PublicationStatistic(models.Model):
    spatialdimensiondate = models.DateField()
    temporaldimensiontype = models.CharField(max_length=50)
    temporaldimensionstartdate = models.DateField()
    temporaldimensionyear= models.IntegerField()
    measure = models.CharField(max_length=50)
    average = models.FloatField()
    standarddeviation = models.FloatField()
    source = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"
