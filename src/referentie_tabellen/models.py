import operator
from functools import reduce

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from referentie_tabellen.referentie_choices import TemporaltypeChoices


class Unit(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=30, default="aantal")
    code = models.CharField(max_length=5, blank=True, null=True)
    symbol = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"


class Theme(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    name_uk = models.CharField(unique=True, max_length=50)
    abbreviation = models.CharField(unique=True, max_length=5)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True)

    excluded_group_prefixes = [
        "modifier_",
        "maintainer",
    ]
    group = models.ForeignKey(
        Group,
        on_delete=models.DO_NOTHING,
        limit_choices_to=~reduce(
            operator.or_,
            [Q(name__startswith=prefix) for prefix in excluded_group_prefixes],
        ),
    )

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        super().clean()

        if self.group_id:
            if any(self.group.name.startswith(prefix) for prefix in self.excluded_group_prefixes):
                prefix_list = '", "'.join(self.excluded_group_prefixes)
                raise ValidationError({"group": f'Group name cannot start with: "{prefix_list}"'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SpatialDimensionType(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(blank=True, null=True, max_length=100)

    def __str__(self):
        return f"{self.name}"


class TemporalDimensionType(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    type = models.IntegerField(
        choices=TemporaltypeChoices.choices,
        default=TemporaltypeChoices.PERIODE,
    )

    def __str__(self):
        return f"{self.name}"


class Source(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    name_long = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
