import datetime

import numpy as np
import pandas as pd
import pytest
from model_bakery import baker

from publicatie_tabellen.publish_observation import (
    _apply_sensitive_rules,
    _get_df_with_filterrule,
)
from referentie_tabellen.models import TemporalDimensionType, Theme, Unit
from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.models.observation import Observation
from statistiek_hub.models.spatial_dimension import SpatialDimension
from statistiek_hub.models.temporal_dimension import TemporalDimension


@pytest.fixture(scope = "function")
def fill_ref_tabellen() -> dict:
    unit = baker.make(Unit, name="aantal")
    theme = baker.make(Theme)

    tempdimtype = baker.make(TemporalDimensionType,  name="Peildatum")
    temp = baker.make(TemporalDimension, startdate=datetime.date(2023, 12, 31), type=tempdimtype)
    spatial = baker.make(SpatialDimension)
    return {'unit': unit, 'theme': theme, 'temp': temp, 'spatial': spatial}


@pytest.mark.parametrize(
    "test_value, test_unit, expected",
    [ (0, 'aantal', 0), (5, 'aantal', 5), (4, 'aantal', 5), 
    (9, 'aantal', 10), (6, 'aantal', 5),
    (None, 'aantal', None), 
    (90, 'percentage', 90), (91, 'percentage', 90), (99, 'percentage', 90),
    (None, 'percentage', None), (np.nan, 'aantal', None),
    (7, 'rapportcijfer', 7), (None, 'rapportcijfer', None)
    ] 
)
def test_apply_sensitive_rules(test_value, test_unit, expected):
    """ change value by rule depending on unit"""
    result = _apply_sensitive_rules(test_value, test_unit)
    assert result == expected

@pytest.mark.parametrize(
    "filter, value_new, base_value, var_value, expected",
    [ ('( $BASE < 10 )', 1, 10 , 50 , [50.0]), 
      ('( $BASE < 10 )', 1, 11 , 50 , [50.0]), 
      ('( $BASE < 10 )', 1, 9 , 50 , [1.0]),
      ('( $BASE < 10 )', None ,  9, 50, [None] ),
      ('( $BASE < 5 )', 10 , 3, 50, [10] ),
      ('( $GEENBASE < 8 )', 1,  3, 50, [] ),
      ('( $BASE < 10 AND $BASE > 5 )', 1, 9 , 50 , [1.0]),
      ('( $BASE < 10 AND $BASE > 5 )', 1, 3 , 50 , [50.0]),
        ] )
@pytest.mark.django_db
def test_get_df_with_filterrule(fill_ref_tabellen, filter, value_new, var_value, base_value, expected):
    """ apply sql db_function public.apply_filter on measure 
        return: dataframe with value corrected by filterrule """
    fixture = fill_ref_tabellen

    # make measures
    measure_base = baker.make(Measure, name='BASE', unit=fixture['unit'])
    measure_var = baker.make(Measure, name='VAR', unit=fixture['unit'])
    # set filter
    filter_var = baker.make(Filter, measure=measure_var, rule = filter, value_new=value_new)
    # make observations
    obs_base = baker.make(Observation, measure=measure_base, temporaldimension=fixture['temp'] , spatialdimension=fixture['spatial'] ,value=base_value)
    obs_var = baker.make(Observation, measure=measure_var, temporaldimension=fixture['temp']  , spatialdimension=fixture['spatial'] , value=var_value)
    
    dftest = _get_df_with_filterrule(measure_var)

    assert dftest['value'].tolist() == expected

    # remove db objects
    measure_base.delete()
    measure_var.delete()
    filter_var.delete()
    obs_base.delete()
    obs_var.delete()


