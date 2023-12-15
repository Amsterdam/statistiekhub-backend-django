import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from referentie_tabellen.models import Theme, Unit
from statistiek_hub.validations import check_code_in_name

from .dimension import Dimension
from .time_stamp_mixin import TimeStampMixin


class Measure(TimeStampMixin):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    label = models.CharField(max_length=75)
    label_uk = models.CharField(max_length=75, blank=True, null=True)
    definition = models.TextField()
    definition_uk = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    calculation = models.CharField(max_length=100, blank=True, null=True)
    sensitive = models.BooleanField(
        default=False,
        help_text="gevoeligedata - afronden en groepsonthulling toepassen",
    )
    unit = models.ForeignKey(Unit, models.RESTRICT)
    decimals = models.IntegerField(default=0)
    source = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)
    theme = models.ForeignKey(Theme, models.RESTRICT)
    dimension = models.ForeignKey(Dimension, models.SET_NULL, blank=True, null=True)
    extra_attr = models.JSONField(
        blank=True, null=True, help_text="jsonfield voor productvelden"
    )
    deprecated = models.BooleanField(default=False, help_text="vervallen")
    deprecated_date = models.DateField(blank=True, null=True)
    deprecated_reason = models.TextField(blank=True, null=True, help_text="toelichting")

    def __str__(self):
        return f"{self.name}"

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

        self.name = self.name.upper()

        if self.unit:
            if self.unit.code:
                self.add_error(
                    errors, {"name": check_code_in_name(self.unit.code, self.name)}
                )
            else:
                pass

        if self.dimension:
            if self.dimension.code:
                self.add_error(
                    errors, {"name": check_code_in_name(self.dimension.code, self.name)}
                )
            else:
                pass

        if self.deprecated == True and not self.deprecated_date:
            self.deprecated_date = datetime.datetime.now().date()

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
