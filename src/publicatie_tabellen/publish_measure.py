import logging

from django.contrib import messages
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F
from django.db.models.query import QuerySet

from publicatie_tabellen.models import PublicationMeasure
from publicatie_tabellen.utils import copy_queryset
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_publishmeasure() -> QuerySet:
    """get queryset from Measure model specificly for publishmeasures"""

    queryset = (
        Measure.objects.select_related("unit")
        .prefetch_related("themes")
        .all()
        .defer("created_at", "updated_at", "id")
        .annotate(
            unit_code=F("unit__code"),
            unit_symbol=F("unit__symbol"),
            theme=ArrayAgg("themes__name", distinct=True),
            theme_uk=ArrayAgg("themes__name_uk", distinct=True),
        )
    )
    return queryset


def publishmeasure() -> tuple:
    """return: tuple(string, django.contrib.messages)"""

    # select measures
    qsmeasure = _get_qs_publishmeasure()

    try:
        truncate(PublicationMeasure)
        copy_queryset(qsmeasure, PublicationMeasure)
        return ("All records for publication-measure are imported", messages.SUCCESS)
    except Exception:  # error
        return ("something went wrong; WARNING table is not updated!", messages.ERROR)
