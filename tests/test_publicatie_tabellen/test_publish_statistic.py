import datetime

import numpy as np
import pytest
from model_bakery import baker

from publicatie_tabellen.publish_observation import publishobservation
from publicatie_tabellen.publish_statistic import (
    _get_df_data_publishstatistic,
    _select_df_wijk_ggw,
)
from publicatie_tabellen.utils import (
    convert_queryset_into_dataframe,
    get_qs_for_bevmin_wonmin,
    set_small_regions_to_nan_if_minimum,
)
from referentie_tabellen.models import SpatialDimensionType, TemporalDimensionType, Unit
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension


@pytest.fixture
def fill_ref_tabellen() -> dict:
    unit = baker.make(Unit, name="aantal")

    tempdimtype = baker.make(TemporalDimensionType, name="Peildatum")
    temppeildatum = baker.make(
        TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype
    )
    tempdimtypejaar = baker.make(TemporalDimensionType, name="Jaar")
    tempjaar = baker.make(
        TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtypejaar
    )

    spatialdimtypewijk = baker.make(SpatialDimensionType, name="Wijk")
    spatialdimtypeggw = baker.make(SpatialDimensionType, name="GGW-gebied")
    spatialdimtypegem = baker.make(SpatialDimensionType, name="Gemeente")
    spatialdimtypebuurt = baker.make(SpatialDimensionType, name="Buurt")
    spatialwijk = baker.make(SpatialDimension, type=spatialdimtypewijk)
    spatialggw = baker.make(SpatialDimension, type=spatialdimtypeggw)
    spatialgem = baker.make(SpatialDimension, type=spatialdimtypegem)
    spatialbuurt = baker.make(SpatialDimension, type=spatialdimtypebuurt)
    return {
        "unit": unit,
        "temppeildatum": temppeildatum,
        "tempjaar": tempjaar,
        "spatialwijk": spatialwijk,
        "spatialggw": spatialggw,
        "spatialgem": spatialgem,
        "spatialbuurt": spatialbuurt,
    }


@pytest.fixture
def fill_bev_won_obs(fill_ref_tabellen):
    fixture = fill_ref_tabellen

    measurebev = baker.make(Measure, name="BEVTOTAAL", unit=fixture["unit"], extra_attr={"BBGA_kleurenpalet": 3})
    obsbev = baker.make(
        Observation,
        measure=measurebev,
        temporaldimension=fixture["temppeildatum"],
        spatialdimension=fixture["spatialwijk"],
        value=1000,
    )
    obsbev2 = baker.make(
        Observation,
        measure=measurebev,
        temporaldimension=fixture["temppeildatum"],
        spatialdimension=fixture["spatialggw"],
        value=1000,
    )
    obsbev3 = baker.make(
        Observation,
        measure=measurebev,
        temporaldimension=fixture["temppeildatum"],
        spatialdimension=fixture["spatialgem"],
        value=1000,
    )
    obsbev4 = baker.make(
        Observation,
        measure=measurebev,
        temporaldimension=fixture["tempjaar"],
        spatialdimension=fixture["spatialgem"],
        value=1000,
    )
    measurewon = baker.make(Measure, name="WVOORRBAG", unit=fixture["unit"], extra_attr={"BBGA_kleurenpalet": 3})
    obswon = baker.make(
        Observation,
        measure=measurewon,
        temporaldimension=fixture["temppeildatum"],
        spatialdimension=fixture["spatialwijk"],
        value=1000,
    )
    obswon2 = baker.make(
        Observation,
        measure=measurewon,
        temporaldimension=fixture["temppeildatum"],
        spatialdimension=fixture["spatialggw"],
        value=1000,
    )
    obswon3 = baker.make(
        Observation,
        measure=measurewon,
        temporaldimension=fixture["temppeildatum"],
        spatialdimension=fixture["spatialgem"],
        value=1000,
    )
    obswon4 = baker.make(
        Observation,
        measure=measurewon,
        temporaldimension=fixture["tempjaar"],
        spatialdimension=fixture["spatialgem"],
        value=1000,
    )



@pytest.mark.parametrize(
    " extra_attr, tempdim, spatialdim, expected",
    [
        ({"BBGA_kleurenpalet": 3}, "temppeildatum", "spatialwijk", 1),
        ({"BBGA_kleurenpalet": 9}, "temppeildatum", "spatialwijk", 0),
        ({"BBGA_kleurenpalet": 4}, "temppeildatum", "spatialwijk", 0),
        ({"BBGA_kleurenpalet": 3}, "tempjaar", "spatialwijk", 0),
        ({"BBGA_kleurenpalet": 3}, "temppeildatum", "spatialbuurt", 0),
        ({}, "temppeildatum", "spatialwijk", 0),
    ],
)
@pytest.mark.django_db
def test_get_df_data_publishstatistic(
    fill_ref_tabellen, extra_attr, tempdim, spatialdim, expected
):
    """check correct filter for select_get_qs_publishstatistic_obs query selection"""
    fixture = fill_ref_tabellen


    measure = baker.make(
        Measure, name="TEST", unit=fixture["unit"], extra_attr=extra_attr
    )
    obs = baker.make(
        Observation,
        measure=measure,
        temporaldimension=fixture[tempdim],
        spatialdimension=fixture[spatialdim],
        value=1000,
    )

    # fill publishobservation model
    _, _ = publishobservation()
    dfobs = _get_df_data_publishstatistic()

    assert len(dfobs) == expected
    if len(dfobs) > 0:
        assert dfobs["spatialdimensiontype"].unique()[0] in [
            "Wijk",
            "GGW-gebied",
            "Gemeente",
        ]

        # check all columns names
        diff = (set(dfobs.columns.values.tolist()) - 
                set(['id', 'spatialdimensiontype', 'spatialdimensiondate',
        'spatialdimensioncode', 'spatialdimensionname', 'temporaldimensiontype',
        'temporaldimensionstartdate', 'temporaldimensionenddate',
        'temporaldimensionyear', 'measure_name', 'value', 'measure_id', 'name',
        'sd_minimum_bevtotaal', 'sd_minimum_wvoorrbag']))

        assert len(diff) == 0

    measure.delete()
    obs.delete()


@pytest.mark.django_db
def test_select_df_wijk_ggw(fill_bev_won_obs):
    """Select only spatialdimension 'Wijk' and 'GGW-gebied'"""
    fixture = fill_bev_won_obs
    # fill publishobservation model
    _, _ = publishobservation()

    dfobs = _get_df_data_publishstatistic()
    assert (
        dfobs["spatialdimensiontype"].unique().sort()
        == ["Wijk", "GGW-gebied", "Gemeente"].sort()
    )

    dfwijkggw = _select_df_wijk_ggw(dfobs)
    assert (
        dfwijkggw["spatialdimensiontype"].unique().sort()
        == ["Wijk", "GGW-gebied"].sort()
    )


@pytest.mark.django_db
def test_get_qs_for_bevmin_wonmin(fill_bev_won_obs):
    """get queryset of observations with only measures, bevtotaal and wvoorrbag,
    for spatialdimensiontype wijk and ggw-gebied
    and temporaldimensiontype 'Peildatum'
    """
    fixture = fill_bev_won_obs

    qsmin = get_qs_for_bevmin_wonmin(Observation)
    assert set(qsmin.values_list("measure__name", flat=True)) == {
        "BEVTOTAAL",
        "WVOORRBAG",
    }
    assert set(qsmin.values_list("spatialdimension__type__name", flat=True)) == {
        "Wijk",
        "GGW-gebied",
    }
    assert set(qsmin.values_list("temporaldimension__type__name", flat=True)) == {
        "Peildatum"
    }


@pytest.mark.parametrize(
    " var_min, extra_attr, spatial, expected",
    [
        (
            "BEVTOTAAL",
            {"BBGA_sd_minimum_bev_totaal": 900, "BBGA_kleurenpalet": 3},
            "spatialwijk",
            10.0,
        ),
        (
            "WVOORRBAG",
            {"BBGA_sd_minimum_wvoor_bag": 900, "BBGA_kleurenpalet": 3},
            "spatialwijk",
            10.0,
        ),
        (
            "BEVTOTAAL",
            {"BBGA_sd_minimum_wvoor_bag": 2000, "BBGA_kleurenpalet": 3},
            "spatialwijk",
            10.0,
        ),
        (
            "WVOORRBAG",
            {"BBGA_sd_minimum_bev_totaal": 2000, "BBGA_kleurenpalet": 3},
            "spatialwijk",
            10.0,
        ),
        (
            "BEVTOTAAL",
            {"BBGA_sd_minimum_bev_totaal": 2000, "BBGA_kleurenpalet": 3},
            "spatialwijk",
            np.nan,
        ),
        (
            "WVOORRBAG",
            {"BBGA_sd_minimum_wvoor_bag": 2000, "BBGA_kleurenpalet": 3},
            "spatialwijk",
            np.nan,
        ),
        (
            "BEVTOTAAL",
            {"BBGA_sd_minimum_bev_totaal": 900, "BBGA_kleurenpalet": 3},
            "spatialggw",
            10.0,
        ),
        (
            "WVOORRBAG",
            {"BBGA_sd_minimum_wvoor_bag": 900, "BBGA_kleurenpalet": 3},
            "spatialggw",
            10.0,
        ),
        (
            "BEVTOTAAL",
            {"BBGA_sd_minimum_bev_totaal": 2000, "BBGA_kleurenpalet": 3},
            "spatialggw",
            np.nan,
        ),
        (
            "WVOORRBAG",
            {"BBGA_sd_minimum_wvoor_bag": 2000, "BBGA_kleurenpalet": 3},
            "spatialggw",
            np.nan,
        ),
        (
            "BEVTOTAAL",
            {
                "BBGA_sd_minimum_bev_totaal": 2000,
                "BBGA_sd_minimum_wvoor_bag": 2000,
                "BBGA_kleurenpalet": 3,
            },
            "spatialggw",
            np.nan,
        ),
    ],
)
@pytest.mark.django_db
def test_set_small_regions_to_nan_if_minimum(
    fill_bev_won_obs, fill_ref_tabellen, var_min, extra_attr, spatial, expected
):
    """set region value to np.nan if var_min is less than minimum_value"""
    fixture = fill_bev_won_obs
    f_ref_tabellen = fill_ref_tabellen

    measurevar = baker.make(
        Measure, name="VAR", unit=f_ref_tabellen["unit"], extra_attr=extra_attr
    )
    obsvar = baker.make(
        Observation,
        measure=measurevar,
        temporaldimension=f_ref_tabellen["temppeildatum"],
        spatialdimension=f_ref_tabellen[spatial],
        value=10,
    )

    # fill publishobservation model
    _, _ = publishobservation()
    dfobs = _get_df_data_publishstatistic()
    qsmin = get_qs_for_bevmin_wonmin(Observation)
    dfmin = convert_queryset_into_dataframe(qsmin)
    dfwijkggw = _select_df_wijk_ggw(dfobs)

    df_result = set_small_regions_to_nan_if_minimum(dfmin, var_min, dfwijkggw)
    assert (
        np.testing.assert_equal(
            df_result[df_result["measure_name"] == "VAR"]["value"].values[0], expected
        )
        is None
    )

    measurevar.delete()
    obsvar.delete()


@pytest.mark.parametrize(
    "bev_value, min_value, expected",
    [ (200, 10, 100.0,),(49, 49, 100.0),(10, 50, np.nan),(np.nan, 50, 100) ],
)
@pytest.mark.django_db
def test_set_small_regions_to_nan_if_minimum_observations(
    fill_ref_tabellen, bev_value, min_value, expected
):
    """set region value to np.nan if var_min is less than minimum_value"""
    f_ref_tabellen = fill_ref_tabellen

    measurebev = baker.make(Measure, name="BEVTOTAAL", unit=f_ref_tabellen["unit"])
    obsbev = baker.make(
        Observation,
        measure=measurebev,
        temporaldimension=f_ref_tabellen["temppeildatum"],
        spatialdimension=f_ref_tabellen["spatialwijk"],
        value=bev_value,
    )

    measurevar = baker.make(Measure, name="VAR", unit=f_ref_tabellen["unit"])
    obsvar = baker.make(
        Observation,
        measure=measurevar,
        temporaldimension=f_ref_tabellen["temppeildatum"],
        spatialdimension=f_ref_tabellen["spatialwijk"],
        value=100,
    )

    # fill publishobservation model
    _, _ = publishobservation()
    dfobs = _get_df_data_publishstatistic()
    print(dfobs)
    qsmin = get_qs_for_bevmin_wonmin(Observation)
    dfmin = convert_queryset_into_dataframe(qsmin)

    df_result = set_small_regions_to_nan_if_minimum(dfmin, "BEVTOTAAL", dfobs, minimum_value=min_value)
    assert (
        np.testing.assert_equal(
            df_result[df_result["measure_name"] == "VAR"]["value"].values[0], expected
        )
        is None
    )

    # dfobs is based on publicationobservation (cleaned-obs) so no nan in df
    if bev_value is not np.nan:
        assert (
            np.testing.assert_equal(
                df_result[df_result["measure_name"] == "BEVTOTAAL"]["value"].values[0], bev_value
            )
            is None
        )
    measurebev.delete()
    obsbev.delete()
    obsvar.delete()
