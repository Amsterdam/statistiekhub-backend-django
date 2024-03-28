import pytest
from model_bakery import baker

from publicatie_tabellen.models import PublicationStatistic
from statistiek_hub.utils.truncate_model import truncate


@pytest.mark.django_db
def test_truncate():
    """truncate db table and restart AutoField primary_key for import"""
    stat = baker.make(PublicationStatistic)
    stat.save()
    assert PublicationStatistic.objects.all().count() == 1
    assert PublicationStatistic.objects.get(pk=1) == stat

    truncate(PublicationStatistic)

    assert PublicationStatistic.objects.all().count() == 0
    # test id reset
    stat.save()
    assert  PublicationStatistic.objects.get(pk=1) == stat
        