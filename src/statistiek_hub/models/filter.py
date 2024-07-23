from django.core.exceptions import ValidationError
from django.db import models

from statistiek_hub.models.model_mixin import AddErrorFuncion
from statistiek_hub.validations import check_filter_rule

from .measure import Measure


class Filter(AddErrorFuncion):
    measure = models.OneToOneField(Measure, on_delete=models.CASCADE, primary_key=True)
    rule = models.TextField()
    value_new = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.measure}"

    def clean(self):
        errors = {}

        self.add_error(
            errors, {"rule": check_filter_rule(self.rule)}
        )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)