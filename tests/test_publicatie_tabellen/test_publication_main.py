import datetime

import pytest
from django.contrib.auth.models import Group
from model_bakery import baker

from publicatie_tabellen.publication_main import PublishFunction
from referentie_tabellen.models import TemporalDimensionType, Theme, Unit
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension


@pytest.fixture
def fill_ref_tabellen() -> dict:
    unit = baker.make(Unit, name="aantal")

    tempdimtype = baker.make(TemporalDimensionType, name="Peildatum")
    temp = baker.make(TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype)
    temp2_startdate = datetime.date(2024, 1, 1)
    temp2 = baker.make(TemporalDimension, startdate=temp2_startdate, type=tempdimtype)

    spatial = baker.make(SpatialDimension)
    return {
        "unit": unit,
        "temp": temp,
        "temp2": temp2,
        "temp2_startdate": temp2_startdate,
        "spatial": spatial,
    }


@pytest.mark.parametrize(
    "calculation, base_value, var1_value, expected",
    [
        ("( ( $VAR1 / ( $BASE ) ) * 1000 )", 10000, 5000, 500.0),
        ("( $VAR1 + $BASE )", 10, 50.5, 60.5),
        ("( $VAR1 -  $BASE )", 100, 80, -20.0),
        ("( ( $VAR1 / ( $BASE + $VAR1 ) ) - 10 )", 5, 3, -9.625),
    ],
)
@pytest.mark.django_db
def test_fill_observationcalculated(fill_ref_tabellen, calculation, var1_value, base_value, expected):
    """fill model ObservationCalculated with observations calculated by the calculation-query of the measure"""
    ficture = fill_ref_tabellen

    measure_calc = baker.make(
        Measure,
        name="CALCVAR",
        calculation=calculation,
        unit=ficture["unit"],
        theme=baker.make(Theme, group=baker.make(Group)),
    )
    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=ficture["unit"],
        theme=baker.make(Theme, group=baker.make(Group)),
    )
    measure_var1 = baker.make(
        Measure,
        name="VAR1",
        unit=ficture["unit"],
        theme=baker.make(Theme, group=baker.make(Group)),
    )

    obs_base = baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=ficture["temp"],
        spatialdimension=ficture["spatial"],
        value=base_value,
    )
    obs_var1 = baker.make(
        Observation,
        measure=measure_var1,
        temporaldimension=ficture["temp2"],
        spatialdimension=ficture["spatial"],
        value=var1_value,
    )

    run = PublishFunction()
    run.fill_observationcalculated()

    qs_result = ObservationCalculated.objects.all()

    assert qs_result.first().value == expected
    assert qs_result.first().temporaldimension.startdate == ficture["temp2_startdate"]  # calc has startdate of var1

    measure_calc.delete()
    measure_base.delete()
    measure_var1.delete()
    obs_base.delete()
    obs_var1.delete()
    qs_result.delete()


@pytest.mark.parametrize(
    "calculation, base_value, var1_value, expected",
    [
        ("( ( $VAR1 / ( $BASE ) ) )", 0, 5, False),
    ],
)
@pytest.mark.django_db
def test_fill_observationcalculated_divide_by_zero(fill_ref_tabellen, calculation, var1_value, base_value, expected):
    """fill model ObservationCalculated with observations calculated by the calculation-query of the measure"""
    ficture = fill_ref_tabellen

    measure_calc = baker.make(
        Measure,
        name="CALCVAR",
        calculation=calculation,
        unit=ficture["unit"],
        theme=baker.make(Theme, group=baker.make(Group)),
    )
    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=ficture["unit"],
        theme=baker.make(Theme, group=baker.make(Group)),
    )
    measure_var1 = baker.make(
        Measure,
        name="VAR1",
        unit=ficture["unit"],
        theme=baker.make(Theme, group=baker.make(Group)),
    )

    obs_base = baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=ficture["temp"],
        spatialdimension=ficture["spatial"],
        value=base_value,
    )
    obs_var1 = baker.make(
        Observation,
        measure=measure_var1,
        temporaldimension=ficture["temp2"],
        spatialdimension=ficture["spatial"],
        value=var1_value,
    )

    run = PublishFunction()
    run.fill_observationcalculated()

    qs_result = ObservationCalculated.objects.all()

    assert qs_result.exists() == expected

    measure_calc.delete()
    measure_base.delete()
    measure_var1.delete()
    obs_base.delete()
    obs_var1.delete()
