from django.core.exceptions import ValidationError
from django.db import models

from statistiek_hub.validations import check_value_context

from .measure import Measure
from .spatial_dimension import SpatialDimension
from .temporal_dimension import TemporalDimension
from .time_stamp_mixin import TimeStampMixin


class Observation(TimeStampMixin):
    class Meta:
        unique_together = [["measure", "spatialdimension", "temporaldimension"]]

    id = models.BigAutoField(primary_key=True)
    measure = models.ForeignKey(Measure, on_delete=models.CASCADE)
    value = models.FloatField()
    temporaldimension = models.ForeignKey(TemporalDimension, on_delete=models.RESTRICT)
    spatialdimension = models.ForeignKey(SpatialDimension, on_delete=models.RESTRICT)

    @classmethod
    def add_error(cls, errors, new_errors):
        for err_code, err_value in new_errors.items():
            if err_value != None:
                if err_code in errors.keys():
                    if isinstance(errors[err_code], ValidationError):
                        errors.update({err_code: [errors[err_code], err_value]})
                    elif isinstance(errors[err_code], list):
                        errors[err_code].append(err_value)
                else:
                    errors.update(new_errors)
        return errors

    def clean(self):
        errors = {}

        self.add_error(
            errors, {"value": check_value_context(self.measure.unit.code, self.value)}
        )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
