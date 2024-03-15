import datetime

import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from referentie_tabellen.models import TemporalDimensionType
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.temporal_dimension import TemporalDimension


class TestModelSave:
    @pytest.mark.django_db
    def test_save_temporaldimension_cbs_date(self):
        """cbs_date should result in year+1"""
        tempdimtype = baker.make(TemporalDimensionType,  name="Peildatum")
        cbs_date = baker.make(TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype)
        assert TemporalDimension.objects.get(pk=1).year == 2024

        cbs_date.delete()
        assert not TemporalDimension.objects.filter(pk=1).exists()

    @pytest.mark.django_db
    def test_save_measure_name_upper(self):
        """name should be saved upper"""
        name_upper = baker.make(Measure, name="test")
        assert Measure.objects.get(pk=1).name == "TEST"

        name_upper.delete()
        assert not Measure.objects.filter(pk=1).exists()

