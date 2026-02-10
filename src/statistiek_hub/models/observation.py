from django.core.exceptions import ValidationError
from django.db import models

from statistiek_hub.validations import check_value_context

from .measure import Measure
from .model_mixin import AddErrorFuncion, TimeStampMixin
from .spatial_dimension import SpatialDimension
from .temporal_dimension import TemporalDimension


class ObservationBase(TimeStampMixin, AddErrorFuncion):
    class Meta:
        abstract = True

    measure = models.ForeignKey(Measure, related_name="+", on_delete=models.CASCADE)
    value = models.FloatField()
    temporaldimension = models.ForeignKey(TemporalDimension, related_name="+", on_delete=models.RESTRICT)
    spatialdimension = models.ForeignKey(SpatialDimension, related_name="+", on_delete=models.RESTRICT)

    def clean(self):
        errors = {}

        self.add_error(errors, {"value": check_value_context(self.measure.unit.code, self.value)})

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

    measure = models.ForeignKey(Measure, related_name="obs_measure", on_delete=models.CASCADE)
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

    measure = models.ForeignKey(Measure, related_name="calc_obs_measure", on_delete=models.CASCADE)
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
