from datetime import date

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker
from tablib import Dataset

from referentie_tabellen.referentie_choices import TemporaltypeChoices
from statistiek_hub.models.measure import Measure
from statistiek_hub.resources.observation_resource import ObservationResource


@pytest.mark.django_db
def test_observation_resource_rejects_deprecated_measure_import():
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

    dataset = Dataset()
    dataset.headers = [
        "measure",
        "spatial_code",
        "spatial_type",
        "spatial_date",
        "temporal_type",
        "temporal_date",
        "value",
    ]
    dataset.append(["OLD_VAR", "A1", "WIJK", "2024-01-01", "JAAR", "2024-01-01", "12"])

    resource = ObservationResource()

    with pytest.raises(ValidationError) as exc_info:
        resource.before_import(dataset)

    assert "measure_deprecated" in exc_info.value.message_dict
    assert "OLD_VAR" in exc_info.value.message_dict["measure_deprecated"][0]
    assert len(dataset) == 0
