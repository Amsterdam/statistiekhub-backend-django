from django.core.exceptions import ValidationError
from django.db import models

from referentie_tabellen.models import TemporalDimensionType
from statistiek_hub.utils.datetime import add_timedelta, set_year


class TemporalDimension(models.Model):
    class Meta:
        indexes = [
            models.Index("type", "startdate", name="unique_temporaldimension_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                name="duplicate_tempdim_constraint",
                fields=["type", "startdate"],
            )
        ]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, editable=False)
    type = models.ForeignKey(TemporalDimensionType, on_delete=models.RESTRICT)
    startdate = models.DateField()
    enddate = models.DateField(editable=False)
    year = models.PositiveIntegerField(editable=False)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    def calc_enddate(self):
        self.enddate = add_timedelta(self.startdate, self.type)

    def clean(self):
        # check enddate
        if not self.calc_enddate():
            print("add_timedelta bestaat niet")
            raise ValidationError(
                "Type bestaat niet in add_timedelta function, neem contact op als de Type opgenomen dient te worden in de add_timedelta function"
            )

    def save(self, *args, **kwargs):
        self.calc_enddate()
        # set year
        self.year = set_year(self.startdate)

        self.name = f"{self.type}: {self.startdate.strftime('%Y-%m-%d')}-->{self.enddate.strftime('%Y-%m-%d')}"
        return super().save(*args, **kwargs)
