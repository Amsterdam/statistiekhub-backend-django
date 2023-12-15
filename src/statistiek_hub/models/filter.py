from django.db import models

from .measure import Measure


class Filter(models.Model):
    id = models.BigAutoField(primary_key=True)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE)
    rule = models.TextField()
    value_new = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.measure}"
