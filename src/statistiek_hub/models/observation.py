from django.core.exceptions import ValidationError
from django.db import models

from statistiek_hub.validations import check_value_context

from .measure import Measure
from .spatial_dimension import SpatialDimension
from .temporal_dimension import TemporalDimension
from .time_stamp_mixin import TimeStampMixin


class ObservationBase(TimeStampMixin):
    class Meta:
        abstract = True

    measure = models.ForeignKey(Measure, related_name="+", on_delete=models.CASCADE)
    value = models.FloatField()
    temporaldimension = models.ForeignKey(
        TemporalDimension, related_name="+", on_delete=models.RESTRICT
    )
    spatialdimension = models.ForeignKey(
        SpatialDimension, related_name="+", on_delete=models.RESTRICT
    )

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


class Observation(ObservationBase):
    class Meta:
        indexes = [
            models.Index(
                "measure",
                "spatialdimension",
                "temporaldimension",
                name="unique_observation_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                name="duplicate_observation_constraint",
                fields=["measure", "spatialdimension", "temporaldimension"],
            )
        ]

    measure = models.ForeignKey(
        Measure, related_name="obs_measure", on_delete=models.CASCADE
    )
    temporaldimension = models.ForeignKey(
        TemporalDimension,
        related_name="obs_temporaldimension",
        on_delete=models.RESTRICT,
    )
    spatialdimension = models.ForeignKey(
        SpatialDimension, related_name="obs_spatialdimension", on_delete=models.RESTRICT
    )


class ObservationCalculated(ObservationBase):
    class Meta:
        indexes = [
            models.Index(
                "measure",
                "spatialdimension",
                "temporaldimension",
                name="unique_calc_observation_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                name="duplicate_calc_observation_constraint",
                fields=["measure", "spatialdimension", "temporaldimension"],
            )
        ]
        verbose_name_plural = "observations calculated"

    measure = models.ForeignKey(
        Measure, related_name="calc_obs_measure", on_delete=models.CASCADE
    )
    temporaldimension = models.ForeignKey(
        TemporalDimension,
        related_name="calc_obs_temporaldimension",
        on_delete=models.RESTRICT,
    )
    spatialdimension = models.ForeignKey(
        SpatialDimension,
        related_name="calc_obs_spatialdimension",
        on_delete=models.RESTRICT,
    )
