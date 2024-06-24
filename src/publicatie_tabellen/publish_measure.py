import logging

from django.contrib import messages
from django.db.models import F

from publicatie_tabellen.models import PublicationMeasure

from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.truncate_model import truncate

logger = logging.getLogger(__name__)


def _copy_queryset(queryset, copy_to_model):
    """ copy queryset into the copy_to_model"""
    new_item_list = []

    for item_obj in queryset:
        new_item_list.append(item_obj)

    copy_to_model.objects.bulk_create(new_item_list)  


def publishmeasure() -> tuple:
    """return: tuple(string, django.contrib.messages)"""

    queryset = Measure.objects.select_related("theme", "unit").all()\
                .defer("created_at", "updated_at", "owner_id", "id")\
                .annotate(theme_uk=F('theme__name_uk'), 
                        unit_code=F('unit__code'), 
                        unit_symbol=F('unit__symbol')
                        )
    try:
        truncate(PublicationMeasure)
        _copy_queryset(queryset, PublicationMeasure)
        return (f"All records for publish-measure are imported", messages.SUCCESS)
    except: # error
        return (f"something went wrong; WARNING table is not updated!", messages.ERROR)