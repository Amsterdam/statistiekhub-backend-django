import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from django.contrib import messages
from django.contrib.auth.models import Group
from model_bakery import baker

import publicatie_tabellen.publish_observation as publish_observation_module
from publicatie_tabellen.models import PublicationObservation
from publicatie_tabellen.publish_observation import (
    _apply_filterrule_if_present,
    _apply_sensitive_if_needed,
    _apply_sensitive_rules,
    _build_measure_dataframe,
    _finalize_and_save_measure_observations,
    _get_df_with_filterrule,
    _get_measures_for_publish,
    publishobservation,
)
from referentie_tabellen.models import TemporalDimensionType, Unit
from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation, ObservationCalculated
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension


@pytest.fixture
def fill_ref_tabellen() -> dict:
    unit = baker.make(Unit, name="aantal")
    tempdimtype = baker.make(TemporalDimensionType, name="Peildatum")
    temp = baker.make(TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype)
    spatial = baker.make(SpatialDimension)
    return {"unit": unit, "temp": temp, "spatial": spatial, "tempdimtype": tempdimtype}


@pytest.mark.parametrize(
    "test_value, test_unit, expected",
    [
        (0, "aantal", 0),
        (5, "aantal", 5),
        (4, "aantal", 5),
        (9, "aantal", 10),
        (6, "aantal", 5),
        (None, "aantal", None),
        (90, "percentage", 90),
        (91, "percentage", 90),
        (99, "percentage", 90),
        (None, "percentage", None),
        (np.nan, "aantal", None),
        (7, "rapportcijfer", 7),
        (None, "rapportcijfer", None),
    ],
)
def test_apply_sensitive_rules(test_value, test_unit, expected):
    """change value by rule depending on unit"""
    result = _apply_sensitive_rules(test_value, test_unit)
    assert result == expected


def test_apply_sensitive_if_needed_returns_unchanged_when_not_sensitive():
    mdf = pd.DataFrame(
        [
            {
                "temporaldimensionyear": 2024,
                "spatialdimensiondate": "2024-01-01",
                "spatialdimensioncode": "A",
                "measure_name": "SENSITIVE_VAR",
                "unit": "percentage",
                "value": 95.0,
            }
        ]
    )

    dfmin = pd.DataFrame(
        [
            {
                "temporaldimensionyear": 2024,
                "spatialdimensiondate": "2024-01-01",
                "spatialdimensioncode": "A",
                "measure_name": "BEVTOTAAL",
                "value": 49,
            }
        ]
    )

    measure = SimpleNamespace(sensitive=False)
    result = _apply_sensitive_if_needed(mdf, measure, dfmin)

    assert result is mdf
    assert result.loc[0, "value"] == 95.0


def test_apply_sensitive_if_needed_applies_sensitive_and_small_region_rule():
    mdf = pd.DataFrame(
        [
            {
                "temporaldimensionyear": 2024,
                "spatialdimensiondate": "2024-01-01",
                "spatialdimensioncode": "A",
                "measure_name": "SENSITIVE_VAR",
                "unit": "percentage",
                "value": 95.0,
            },
            {
                "temporaldimensionyear": 2024,
                "spatialdimensiondate": "2024-01-01",
                "spatialdimensioncode": "B",
                "measure_name": "SENSITIVE_VAR",
                "unit": "percentage",
                "value": 95.0,
            },
        ]
    )

    dfmin = pd.DataFrame(
        [
            {
                "temporaldimensionyear": 2024,
                "spatialdimensiondate": "2024-01-01",
                "spatialdimensioncode": "A",
                "measure_name": "BEVTOTAAL",
                "value": 49,
            },
            {
                "temporaldimensionyear": 2024,
                "spatialdimensiondate": "2024-01-01",
                "spatialdimensioncode": "B",
                "measure_name": "BEVTOTAAL",
                "value": 50,
            },
        ]
    )

    measure = SimpleNamespace(sensitive=True)
    result = _apply_sensitive_if_needed(mdf, measure, dfmin)

    # First: sensitive rule caps percentage >= 90 to 90.
    # Then: values for regions with < 50 inhabitants become NaN.
    assert np.isnan(result.loc[result["spatialdimensioncode"] == "A", "value"].iloc[0])
    assert result.loc[result["spatialdimensioncode"] == "B", "value"].iloc[0] == 90.0


def test_publishobservation_includes_warning_for_measure_without_data(monkeypatch):
    measure_no_data = SimpleNamespace(name="NO_DATA", sensitive=False)

    monkeypatch.setattr(
        publish_observation_module,
        "_get_dfmin_for_sensitive_rules",
        lambda: pd.DataFrame(),
    )
    monkeypatch.setattr(
        publish_observation_module,
        "_get_measures_for_publish",
        lambda: [measure_no_data],
    )
    monkeypatch.setattr(
        publish_observation_module,
        "_build_measure_dataframe",
        lambda measure: (pd.DataFrame(), None),
    )
    monkeypatch.setattr(publish_observation_module, "truncate", lambda model: None)

    msg, level = publish_observation_module.publishobservation()
    assert level == messages.SUCCESS
    assert "WARNING" in msg
    assert "NO_DATA" in msg


@pytest.mark.parametrize(
    "filter, value_new, base_value, var_value, expected",
    [
        ("( $BASE < 10 )", 1, 10, 50, [50.0]),
        ("( $BASE < 10 )", 1, 11, 50, [50.0]),
        ("( $BASE < 10 )", 1, 9, 50, [1.0]),
        ("( $BASE < 10 )", None, 9, 50, [None]),
        ("( $BASE < 5 )", 10, 3, 50, [10]),
        ("( $GEENBASE < 8 )", 1, 3, 50, []),
        ("( $BASE < 10 AND $BASE > 5 )", 1, 9, 50, [1.0]),
        ("( $BASE < 10 AND $BASE > 5 )", 1, 3, 50, [50.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 3, 50, [1.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 6, 3, [1.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 6, 50, [50.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 0, 50, [50.0]),
    ],
)
@pytest.mark.django_db
def test_get_df_with_filterrule(fill_ref_tabellen, filter, value_new, var_value, base_value, expected):
    """apply sql db_function public.apply_filter on measure
    return: dataframe with value corrected by filterrule"""
    fixture = fill_ref_tabellen

    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=fixture["unit"],
        team=baker.make(Group),
    )
    measure_var = baker.make(
        Measure,
        name="VAR",
        unit=fixture["unit"],
        team=baker.make(Group),
    )

    filter_var = baker.make(Filter, measure=measure_var, rule=filter, value_new=value_new)

    obs_base = baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=base_value,
    )
    obs_var = baker.make(
        Observation,
        measure=measure_var,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=var_value,
    )

    dftest = _get_df_with_filterrule(measure_var, calculated_years=None)

    assert dftest["value"].tolist() == expected

    measure_base.delete()
    measure_var.delete()
    filter_var.delete()
    obs_base.delete()
    obs_var.delete()


@pytest.mark.parametrize(
    "filter, value_new, base_value, var_value, expected",
    [
        ("( $BASE < 10 )", 1, 11, 50, [50.0]),
        ("( $BASE < 10 )", 1, 9, 50, [1.0]),
        ("( $BASE < 10 )", None, 9, 50, [None]),
        ("( $BASE < 5 )", 10, 3, 50, [10]),
        ("( $GEENBASE < 8 )", 1, 3, 50, []),
        ("( $BASE < 10 AND $BASE > 5 )", 1, 9, 50, [1.0]),
        ("( $BASE < 10 AND $BASE > 5 )", 1, 3, 50, [50.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 3, 50, [1.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 6, 3, [1.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 6, 50, [50.0]),
        ("( ( ( $BASE != 0 ) AND ( $BASE < 5 ) ) OR ( $VAR < 5 ) )", 1, 0, 50, [50.0]),
    ],
)
@pytest.mark.django_db
def test_get_df_with_filterrule_on_calcobs(fill_ref_tabellen, filter, value_new, var_value, base_value, expected):
    """apply sql db_function public.apply_filter on measure
    return: dataframe with value corrected by filterrule"""
    fixture = fill_ref_tabellen

    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=fixture["unit"],
        team=baker.make(Group),
    )
    measure_var = baker.make(
        Measure,
        name="VAR",
        unit=fixture["unit"],
        team=baker.make(Group),
    )

    filter_var = baker.make(Filter, measure=measure_var, rule=filter, value_new=value_new)

    obs_base = baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=base_value,
    )

    obs_var = baker.make(
        ObservationCalculated,
        measure=measure_var,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=var_value,
    )

    dftest = _get_df_with_filterrule(measure_var, calculated_years=[2024])
    assert dftest["value"].tolist() == expected

    # als calculated_years = [] dan geen observations vanuit ObservationCalculated
    dftest = _get_df_with_filterrule(measure_var, calculated_years=[])
    assert dftest["value"].tolist() == []

    measure_base.delete()
    measure_var.delete()
    filter_var.delete()
    obs_base.delete()
    obs_var.delete()


@pytest.mark.parametrize(
    "filter, basis_start_date, var_start_date, expected_start_date",
    [
        (
            "( $BASE < 10 )",
            datetime.date(2023, 4, 10),
            datetime.date(2023, 1, 10),
            "Peildatum: 2023-01-10-->2023-01-10",
        ),
        (
            "( $BASE < 10 )",
            datetime.date(2023, 12, 10),
            datetime.date(2023, 10, 10),
            "Peildatum: 2023-10-10-->2023-10-10",
        ),
        (
            "( $BASE < 10 )",
            datetime.date(2023, 12, 4),
            datetime.date(2023, 12, 29),
            "Peildatum: 2023-12-29-->2023-12-29",
        ),
    ],
)
@pytest.mark.django_db
def test_get_df_filterrule_with_difftempdate(
    fill_ref_tabellen, filter, basis_start_date, var_start_date, expected_start_date
):
    """apply sql db_function public.apply_filter on measure
    return: dataframe with timestamp from VAR measure"""
    fixture = fill_ref_tabellen

    temp1 = baker.make(TemporalDimension, startdate=basis_start_date, type=fixture["tempdimtype"])
    temp2 = baker.make(TemporalDimension, startdate=var_start_date, type=fixture["tempdimtype"])

    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=fixture["unit"],
        team=baker.make(Group),
    )
    measure_var = baker.make(
        Measure,
        name="VAR",
        unit=fixture["unit"],
        team=baker.make(Group),
    )

    filter_var = baker.make(Filter, measure=measure_var, rule=filter, value_new=None)

    obs_base = baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=temp1,
        spatialdimension=fixture["spatial"],
        value=5,
    )
    obs_var = baker.make(
        Observation,
        measure=measure_var,
        temporaldimension=temp2,
        spatialdimension=fixture["spatial"],
        value=100,
    )

    dftest = _get_df_with_filterrule(measure_var, calculated_years=None)

    assert dftest["value"].tolist() == [None]
    temp_id = dftest["temporaldimension_id"].item()
    assert str(TemporalDimension.objects.get(pk=temp_id)) == expected_start_date

    measure_base.delete()
    measure_var.delete()
    filter_var.delete()
    obs_base.delete()
    obs_var.delete()
    temp1.delete()
    temp2.delete()


@pytest.mark.parametrize(
    "decimals, base_value, expected",
    [
        (0, 50.23, [50.0]),
        (1, 50.23, [50.2]),
        (2, 50.236, [50.24]),
        (2, 50.235, [50.24]),
        (2, 50.234, [50.23]),
        (2, 50.2250, [50.22]),
        (2, 50.2353, [50.24]),
        (2, 50.2254, [50.23]),
        (2, 50.2356, [50.24]),
        (1, np.nan, []),
        (0, np.nan, []),
    ],
)
@pytest.mark.django_db
def test_set_decimals(fill_ref_tabellen, decimals, base_value, expected):
    """apply set decimals on the value's of a measure
    return:"""
    fixture = fill_ref_tabellen

    unit = baker.make(Unit, name="percentage")
    measure = baker.make(
        Measure,
        name="BASE",
        unit=unit,
        decimals=decimals,
        team=baker.make(Group),
    )

    obs = baker.make(
        Observation,
        measure=measure,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=base_value,
    )

    mdf, _ = _build_measure_dataframe(measure)
    _finalize_and_save_measure_observations(mdf)

    result = PublicationObservation.objects.values_list("value", flat=True)
    assert list(result) == expected

    measure.delete()
    obs.delete()


@pytest.mark.django_db
def test_build_measure_dataframe_adds_missing_calculated_years(fill_ref_tabellen):
    fixture = fill_ref_tabellen

    temp_2023 = baker.make(
        TemporalDimension,
        startdate=datetime.date(2023, 1, 1),
        type=fixture["tempdimtype"],
    )
    temp_2024 = baker.make(
        TemporalDimension,
        startdate=datetime.date(2024, 1, 31),
        type=fixture["tempdimtype"],
    )

    measure = baker.make(
        Measure,
        name="CALC_MEASURE",
        unit=fixture["unit"],
        team=baker.make(Group),
        calculation="( $BASE + $VAR )",
    )

    baker.make(
        Observation,
        measure=measure,
        temporaldimension=temp_2023,
        spatialdimension=fixture["spatial"],
        value=1,
    )
    baker.make(
        ObservationCalculated,
        measure=measure,
        temporaldimension=temp_2023,
        spatialdimension=fixture["spatial"],
        value=10,
    )
    baker.make(
        ObservationCalculated,
        measure=measure,
        temporaldimension=temp_2024,
        spatialdimension=fixture["spatial"],
        value=20,
    )

    mdf, calculated_years = _build_measure_dataframe(measure)

    assert len(mdf) == 2
    assert set(mdf["temporaldimensionyear"].tolist()) == {2023, 2024}
    assert calculated_years == [2024]


@pytest.mark.django_db
def test_deprecated_measure_is_included_and_can_be_published(fill_ref_tabellen):
    fixture = fill_ref_tabellen

    measure = baker.make(
        Measure,
        name="DEPRECATED_MEASURE",
        unit=fixture["unit"],
        team=baker.make(Group),
        deprecated=True,
    )
    baker.make(
        Observation,
        measure=measure,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=123,
    )

    assert measure.id in set(_get_measures_for_publish().values_list("id", flat=True))

    mdf, _ = _build_measure_dataframe(measure)
    assert _finalize_and_save_measure_observations(mdf) is True
    assert PublicationObservation.objects.filter(measure=measure.name).exists()


@pytest.mark.django_db
def test_apply_filterrule_if_present_merges_and_publishes(fill_ref_tabellen):
    fixture = fill_ref_tabellen

    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=fixture["unit"],
        team=baker.make(Group),
    )
    measure_var = baker.make(
        Measure,
        name="VAR",
        unit=fixture["unit"],
        team=baker.make(Group),
    )
    baker.make(Filter, measure=measure_var, rule="( $BASE < 10 )", value_new=1)

    baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=9,
    )
    baker.make(
        Observation,
        measure=measure_var,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=50,
    )

    mdf, calculated_years = _build_measure_dataframe(measure_var)
    mdf = _apply_filterrule_if_present(mdf, measure_var, calculated_years)
    assert _finalize_and_save_measure_observations(mdf) is True

    assert list(PublicationObservation.objects.values_list("value", flat=True)) == [1.0]


@pytest.mark.django_db
def test_publishobservation_happy_flow_end_to_end(fill_ref_tabellen):
    fixture = fill_ref_tabellen

    measure_base = baker.make(
        Measure,
        name="BASE",
        unit=fixture["unit"],
        decimals=1,
        sensitive=False,
        team=baker.make(Group),
    )
    measure_var = baker.make(
        Measure,
        name="VAR",
        unit=fixture["unit"],
        decimals=0,
        sensitive=False,
        team=baker.make(Group),
    )
    baker.make(Filter, measure=measure_var, rule="( $BASE < 10 )", value_new=1)

    baker.make(
        Observation,
        measure=measure_base,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=9.12,
    )
    baker.make(
        Observation,
        measure=measure_var,
        temporaldimension=fixture["temp"],
        spatialdimension=fixture["spatial"],
        value=50,
    )

    publishobservation()

    rows = list(PublicationObservation.objects.values_list("measure", "value"))
    assert dict(rows) == {"BASE": 9.1, "VAR": 1.0}
