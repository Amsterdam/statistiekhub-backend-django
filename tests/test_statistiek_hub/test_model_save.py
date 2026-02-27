import datetime

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from referentie_tabellen.models import TemporalDimensionType, Unit
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension


class TestModelSave:
    @pytest.mark.django_db
    def test_save_temporaldimension_cbs_date(self):
        """cbs_date should result in year+1"""
        tempdimtype = baker.make(TemporalDimensionType, name="Peildatum")
        cbs_date = baker.make(TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype)
        assert TemporalDimension.objects.first().year == 2024

        cbs_date.delete()
        assert not TemporalDimension.objects.exists()

    @pytest.mark.django_db
    def test_clean_raises_validation_error(self):
        """temporaltype doesnt exist"""
        tempdimtype = baker.make(TemporalDimensionType, name="bestaatniet")

        temp_date = TemporalDimension(startdate=datetime.date(2023, 12, 31), type=tempdimtype)

        with pytest.raises(ValidationError) as e:
            temp_date.clean()

        assert "Type bestaat niet in add_timedelta function" in str(e.value)

    @pytest.mark.django_db
    def test_save_measure_name_upper(self):
        """name should be saved upper"""
        name_upper = baker.make(Measure, name="test2", team=baker.make(Group))
        assert Measure.objects.first().name == "TEST2"

        name_upper.delete()
        assert not Measure.objects.exists()

    @pytest.mark.django_db
    def test_save_observation_validationerror(self):
        """percentage bigger than 200 -> result in validationerror"""

        unit_var = baker.make(Unit, name="percentage", code="P")
        measure_var = baker.make(
            Measure,
            name="VAR",
            unit=unit_var,
            team=baker.make(Group),
        )

        tempdimtype = baker.make(TemporalDimensionType, name="Peildatum")
        temp = baker.make(TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype)
        spatial = baker.make(SpatialDimension)

        # check the specific error message
        with pytest.raises(ValidationError) as excinfo:
            baker.make(
                Observation,
                measure=measure_var,
                temporaldimension=temp,
                spatialdimension=spatial,
                value=1001,
            )
        assert "Percentage is more than 1000" in str(excinfo.value)
