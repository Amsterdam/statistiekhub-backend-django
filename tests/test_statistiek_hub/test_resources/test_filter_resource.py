import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker
from tablib import Dataset

from referentie_tabellen.referentie_choices import TemporaltypeChoices
from statistiek_hub.models.measure import Measure
from statistiek_hub.resources.filter_resource import FilterResource


@pytest.mark.django_db
def test_filter_resource_rejects_deprecated_measure_import():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make("auth.Group")
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

    dataset = Dataset()
    dataset.headers = ["measure", "rule", "value_new"]
    dataset.append(["OLD_VAR", "$OLD_VAR > 10", "5"])

    resource = FilterResource()

    with pytest.raises(ValidationError) as exc_info:
        resource.before_import(dataset)

    assert "measure_deprecated" in exc_info.value.message_dict
    assert "OLD_VAR" in exc_info.value.message_dict["measure_deprecated"][0]


@pytest.mark.django_db
def test_filter_resource_allows_active_measure_import():
    unit = baker.make("referentie_tabellen.Unit", name="aantal")
    team = baker.make("auth.Group")
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

    dataset = Dataset()
    dataset.headers = ["measure", "rule", "value_new"]
    dataset.append(["NEW_VAR", "$NEW_VAR > 10", "5"])

    resource = FilterResource()
    result = resource.import_data(dataset, dry_run=False, raise_errors=False)

    assert result.has_errors() is False
    assert result.has_validation_errors() is False
