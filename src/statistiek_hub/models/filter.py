from django.db import models

from statistiek_hub.models.model_mixin import AddErrorFuncion, TimeStampMixin
from statistiek_hub.validations import validate_filter_rule

from .measure import Measure


class Filter(TimeStampMixin, AddErrorFuncion):
    measure = models.OneToOneField(Measure, on_delete=models.CASCADE, primary_key=True)
    rule = models.TextField(validators=[validate_filter_rule])
    value_new = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.measure}"
