from django.db import models


class TemporaltypeChoices(models.IntegerChoices):
    PEILDATUM = 1, "Peildatum"
    PERIODE = 2, "Periode"
