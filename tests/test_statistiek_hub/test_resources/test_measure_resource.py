from datetime import date

import pytest
from model_bakery import baker
from tablib import Dataset

from referentie_tabellen.models import Theme
from statistiek_hub.resources.measure_resource import (
    MANYTOMANY_SEPARATOR,
    MeasureResource,
    RequiredManyToManyWidget,
)


class TestRequiredManyToManyWidget:
    def setup_method(self):
        self.widget = RequiredManyToManyWidget(Theme, field="name", column_name="theme")

    def test_clean_raises_when_value_blank(self):
        with pytest.raises(ValueError) as exc:
            self.widget.clean("", row={})

        assert "Kolom 'theme' is verplicht" in str(exc.value)

    @pytest.mark.django_db
    def test_clean_returns_queryset_when_all_values_exist(self):
        theme_a = baker.make(Theme, name="Theme A", name_uk="Theme A UK", abbreviation="TA")
        theme_b = baker.make(Theme, name="Theme B", name_uk="Theme B UK", abbreviation="TB")

        value = f"{theme_a.name}{MANYTOMANY_SEPARATOR} {theme_b.name}"
        queryset = self.widget.clean(value)

        assert set(queryset.values_list("id", flat=True)) == {theme_a.id, theme_b.id}

    @pytest.mark.django_db
    def test_clean_raises_value_error_when_theme_missing(self):
        theme = baker.make(Theme, name="Theme C", name_uk="Theme C UK", abbreviation="TC")
        missing_theme = "Missing Theme"

        value = f"{theme.name}{MANYTOMANY_SEPARATOR}{missing_theme}"

        with pytest.raises(ValueError) as exc:
            self.widget.clean(value)

        message = str(exc.value)
        assert missing_theme in message
        assert "kolom 'theme'" in message.lower()


@pytest.mark.parametrize(
    "temporaltype_values, expected",
    [
        (["Peildatum", "periode"], [1, 2]),
        ([" peildatum ", "PERIODE"], [1, 2]),
        (["1", "2"], [1, 2]),
    ],
)
def test_measure_resource_normalizes_temporaltype_labels_case_insensitive(temporaltype_values, expected):
    dataset = Dataset()
    dataset.headers = ["name", "temporaltype"]

    for index, temporaltype_value in enumerate(temporaltype_values, start=1):
        dataset.append([f"MEASURE_{index}", temporaltype_value])

    resource = MeasureResource()
    resource.before_import(dataset)

    assert list(dataset["temporaltype"]) == expected


def test_measure_resource_normalizes_deprecated_date_in_place():
    dataset = Dataset()
    dataset.headers = ["name", "deprecated_date"]
    dataset.append(["MEASURE_1", "2026-07-21"])

    resource = MeasureResource()
    resource.before_import(dataset)

    assert list(dataset["deprecated_date"]) == [date(2026, 7, 21)]
