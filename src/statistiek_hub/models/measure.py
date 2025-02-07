import datetime

from django.core.exceptions import ValidationError
from django.db import models

from referentie_tabellen.models import Theme, Unit
from statistiek_hub.validations import check_code_in_name, validate_calculation_string

from .dimension import Dimension
from .model_mixin import AddErrorFuncion, TimeStampMixin


class Measure(TimeStampMixin, AddErrorFuncion):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    label = models.CharField(max_length=75)
    label_uk = models.CharField(max_length=75, blank=True, default="")
    definition = models.TextField()
    definition_uk = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    calculation = models.CharField(max_length=200, blank=True, default="", validators=[validate_calculation_string])
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
    deprecated_reason = models.TextField(
        blank=True, default="", help_text="toelichting"
    )

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        errors = {}

        self.name = self.name.upper()

        # if self.unit:
        #     if self.unit.code:
        #         self.add_error(
        #             errors, {"name": check_code_in_name(self.unit.code, self.name)}
        #         )
        #     else:
        #         pass

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
