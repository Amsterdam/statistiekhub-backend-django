import numpy as np
import pandas as pd
import pytest
from model_bakery import baker

from publicatie_tabellen.models import PublicationMeasure, PublicationObservation
from publicatie_tabellen.publish_measure import _get_qs_publishmeasure
from publicatie_tabellen.utils import (
    convert_queryset_into_dataframe,
    copy_dataframe,
    copy_queryset,
    round_to_base,
)
from statistiek_hub.models.measure import Measure

sample_statistic = {'spatialdimensiondate': ['2022-03-24'],
        'spatialdimensionname': ['Grachtengordel-West'],
        'spatialdimensioncode': ['AA'],
        'spatialdimensiontype': ['Wijk'],
        'temporaldimensiontype':  ['Peildatum'],
        'temporaldimensionstartdate': ['2024-01-01'],
        'temporaldimensionenddate': ['2024-12-01'],
        'temporaldimensionyear': [2024],
        'measure':  ['TEST'],
        'value':  [49.792983]
}


@pytest.mark.parametrize(
    "test_input, expected",
    [ (11,10), (5,5), (2,0), (107,105), (18,20), (-3, -5), (-11, -10) ])
def test_round_to_base(test_input, expected):
    """ round up / down to base """
    assert round_to_base(test_input) == expected

@pytest.mark.django_db
def test_convert_queryset_into_dataframe(qs=None, model=Measure):
    """ converts a queryset into a dataframe """   
    name_test = baker.make(model,  name="TEST")
    qs = model.objects.all()

    df = convert_queryset_into_dataframe(qs)

    assert isinstance(df,pd.DataFrame)
    assert df["name"][0] == "TEST"

    name_test.delete()
    assert not model.objects.exists()

@pytest.mark.django_db
def test_copy_queryset(model=Measure, copy_to_model=PublicationMeasure):
    """ copy queryset into the copy_to_model """
    name_test = baker.make(model,  name="TEST", label="aangemaakt")
    qs_tosave = _get_qs_publishmeasure(model)
    
    copy_queryset(qs_tosave, copy_to_model)
    
    qs_copy_to_model = copy_to_model.objects.all()
    assert qs_copy_to_model.first().name == "TEST"

    qs_copy_to_model.delete()
    assert not copy_to_model.objects.exists()

    name_test.delete()
    assert not model.objects.exists()

@pytest.mark.django_db
def test_copy_dataframe(test_df=pd.DataFrame(sample_statistic), copy_to_model=PublicationObservation):
    """ copy dataframe into the copy_to_model 
        df.columns must be equal to copy_to_model._fields""" 

    copy_dataframe(test_df, copy_to_model)

    qs = copy_to_model.objects.all()
    assert qs.first().measure == "TEST"

    qs.delete()
    assert not copy_to_model.objects.exists()