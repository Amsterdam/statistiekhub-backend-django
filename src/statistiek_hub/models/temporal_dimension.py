import datetime

from django.db import models

from referentie_tabellen.models import TemporalDimensionType
from statistiek_hub.utils.datetime import add_timedelta


class TemporalDimension(models.Model):
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["type", "startdate"], name="unique_temporaldim"
            )
        ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, editable=False)
    type = models.ForeignKey(TemporalDimensionType, on_delete=models.RESTRICT)
    startdate = models.DateTimeField(default=datetime.datetime(2023, 1, 1, 0, 0, 0))
    enddate = models.DateTimeField(editable=False)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.enddate = add_timedelta(self.startdate, self.type)
        self.name = f"{self.type}: {self.startdate.strftime('%Y-%m-%d')}-->{self.enddate.strftime('%Y-%m-%d')}"
        return super().save(*args, **kwargs)
