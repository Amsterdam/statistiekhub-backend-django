import logging

from django.contrib import messages
from django.db.models import F
from django.db.models.query import QuerySet

from publicatie_tabellen.models import PublicationMeasure
from publicatie_tabellen.utils import copy_queryset
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _get_qs_publishmeasure(obsmodel=Measure) -> QuerySet:
    """get queryset from obsmodel specificly for publishmeasures"""

    queryset = (
        obsmodel.objects.select_related("theme", "unit")
        .all()
        .defer("created_at", "updated_at", "owner_id", "id")
        .annotate(
            theme_uk=F("theme__name_uk"),
            unit_code=F("unit__code"),
            unit_symbol=F("unit__symbol"),
        )
    )
    return queryset


def publishmeasure() -> tuple:
    """return: tuple(string, django.contrib.messages)"""

    # select measures
    qsmeasure = _get_qs_publishmeasure(Measure)

    try:
        truncate(PublicationMeasure)
        copy_queryset(qsmeasure, PublicationMeasure)
        return (f"All records for publication-measure are imported", messages.SUCCESS)
    except:  # error
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR)
