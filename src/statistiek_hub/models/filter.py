from django.db import models

from .measure import Measure


class Filter(models.Model):
    measure = models.OneToOneField(Measure, on_delete=models.CASCADE, primary_key=True)
    rule = models.TextField()
    value_new = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.measure}"

    #TODO validate the rule -> bestaat measure, bv is measure een aantal (met percentages als basis is raar?) hoe om te gaan met OR en AND?