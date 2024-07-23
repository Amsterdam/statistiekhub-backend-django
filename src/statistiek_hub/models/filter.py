from django.db import models
from django.core.exceptions import ValidationError

from statistiek_hub.validations import check_filter_rule

from .measure import Measure


class Filter(models.Model):
    measure = models.OneToOneField(Measure, on_delete=models.CASCADE, primary_key=True)
    rule = models.TextField()
    value_new = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.measure}"

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
            errors, {"rule": check_filter_rule(self.rule)}
        )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)