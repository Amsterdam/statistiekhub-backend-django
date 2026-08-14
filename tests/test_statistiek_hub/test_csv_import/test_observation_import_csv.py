from datetime import date

import pandas as pd
import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from referentie_tabellen.referentie_choices import TemporaltypeChoices
from statistiek_hub.csv_import.observation.import_csv import pre_import
from statistiek_hub.models.measure import Measure


@pytest.mark.django_db
def test_pre_import_rejects_deprecated_measure():
    spatial_type = baker.make("referentie_tabellen.SpatialDimensionType", name="WIJK")
    temporal_type = baker.make(
        "referentie_tabellen.TemporalDimensionType",
        name="Jaar",
        type=TemporaltypeChoices.PEILDATUM,
    )
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)

    baker.make(
        Measure,
        name="OLD_VAR",
        label="Deprecated variable",
        definition="Deprecated variable",
        unit=unit,
        team=team,
        deprecated=True,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )

    baker.make(
        "statistiek_hub.SpatialDimension",
        code="A1",
        type=spatial_type,
        source_date=date(2024, 1, 1),
    )
    baker.make(
        "statistiek_hub.TemporalDimension",
        type=temporal_type,
        startdate=date(2024, 1, 1),
    )

    df = pd.DataFrame(
        [
            {
                "measure": "OLD_VAR",
                "spatial_code": "A1",
                "spatial_type": "WIJK",
                "spatial_date": "2024-01-01",
                "temporal_type": "JAAR",
                "temporal_date": "2024-01-01",
                "value": "12",
            }
        ]
    )

    with pytest.raises(ValidationError) as exc_info:
        pre_import(df=df)

    messages = [message for error in exc_info.value.error_list for message in error.messages]
    assert any("Deprecated measures are not allowed" in message for message in messages)
    assert any("OLD_VAR" in message for message in messages)


@pytest.mark.django_db
def test_pre_import_rejects_file_when_mixed_deprecated_and_active_measure():
    spatial_type = baker.make("referentie_tabellen.SpatialDimensionType", name="WIJK")
    temporal_type = baker.make(
        "referentie_tabellen.TemporalDimensionType",
        name="Jaar",
        type=TemporaltypeChoices.PEILDATUM,
    )
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make(Group)

    baker.make(
        Measure,
        name="OLD_VAR",
        label="Deprecated variable",
        definition="Deprecated variable",
        unit=unit,
        team=team,
        deprecated=True,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )
    baker.make(
        Measure,
        name="NEW_VAR",
        label="Active variable",
        definition="Active variable",
        unit=unit,
        team=team,
        deprecated=False,
        temporaltype=TemporaltypeChoices.PEILDATUM,
    )

    baker.make(
        "statistiek_hub.SpatialDimension",
        code="A1",
        type=spatial_type,
        source_date=date(2024, 1, 1),
    )
    baker.make(
        "statistiek_hub.TemporalDimension",
        type=temporal_type,
        startdate=date(2024, 1, 1),
    )

    df = pd.DataFrame(
        [
            {
                "measure": "OLD_VAR",
                "spatial_code": "A1",
                "spatial_type": "WIJK",
                "spatial_date": "2024-01-01",
                "temporal_type": "JAAR",
                "temporal_date": "2024-01-01",
                "value": "12",
            },
            {
                "measure": "NEW_VAR",
                "spatial_code": "A1",
                "spatial_type": "WIJK",
                "spatial_date": "2024-01-01",
                "temporal_type": "JAAR",
                "temporal_date": "2024-01-01",
                "value": "99",
            },
        ]
    )

    with pytest.raises(ValidationError) as exc_info:
        pre_import(df=df)

    messages = [message for error in exc_info.value.error_list for message in error.messages]
    assert any("Deprecated measures are not allowed" in message for message in messages)
    assert any("OLD_VAR" in message for message in messages)
