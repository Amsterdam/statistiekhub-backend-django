from datetime import date

import pytest
from django.contrib.auth.models import Group
from model_bakery import baker
from tablib import Dataset

from referentie_tabellen.models import Source, Theme
from statistiek_hub.models.measure import Measure
from statistiek_hub.resources.measure_resource import (
    MANYTOMANY_SEPARATOR,
    MeasureResource,
    RequiredManyToManyWidget,
)


@pytest.mark.django_db
class TestMeasureResource:
    def setup_method(self):
        self.theme_widget = RequiredManyToManyWidget(Theme, field="name", column_name="theme")

    def test_required_many_to_many_widget_raises_when_value_blank(self):
        with pytest.raises(ValueError) as exc:
            self.theme_widget.clean("", row={})

        assert "Kolom 'theme' is verplicht" in str(exc.value)

    def test_required_many_to_many_widget_returns_queryset_when_all_theme_values_exist(self):
        theme_a = baker.make(Theme, name="Theme A", name_uk="Theme A UK", abbreviation="TA")
        theme_b = baker.make(Theme, name="Theme B", name_uk="Theme B UK", abbreviation="TB")

        value = f"{theme_a.name}{MANYTOMANY_SEPARATOR} {theme_b.name}"
        queryset = self.theme_widget.clean(value)

        assert set(queryset.values_list("id", flat=True)) == {theme_a.id, theme_b.id}

    def test_required_many_to_many_widget_raises_when_theme_missing(self):
        theme = baker.make(Theme, name="Theme C", name_uk="Theme C UK", abbreviation="TC")
        missing_theme = "Missing Theme"

        value = f"{theme.name}{MANYTOMANY_SEPARATOR}{missing_theme}"

        with pytest.raises(ValueError) as exc:
            self.theme_widget.clean(value)

        message = str(exc.value)
        assert missing_theme in message
        assert "kolom 'theme'" in message.lower()

    def test_required_many_to_many_widget_is_case_insensitive_for_theme(self):
        theme_a = baker.make(Theme, name="Theme A", name_uk="Theme A UK", abbreviation="TA")
        theme_b = baker.make(Theme, name="Theme B", name_uk="Theme B UK", abbreviation="TB")

        value = f"{theme_a.name.lower()}{MANYTOMANY_SEPARATOR} {theme_b.name.upper()}"
        queryset = self.theme_widget.clean(value)

        assert set(queryset.values_list("id", flat=True)) == {theme_a.id, theme_b.id}

    def test_required_many_to_many_widget_is_case_insensitive_for_source(self):
        widget = RequiredManyToManyWidget(Source, field="name", column_name="source")
        source_a = baker.make(Source, name="Source A", name_long="Source A Long")
        source_b = baker.make(Source, name="Source B", name_long="Source B Long")

        value = f"{source_a.name.lower()}{MANYTOMANY_SEPARATOR}{source_b.name.upper()}"
        queryset = widget.clean(value)

        assert set(queryset.values_list("id", flat=True)) == {source_a.id, source_b.id}

    @pytest.mark.parametrize(
        "temporaltype_values, expected",
        [
            (["Peildatum", "periode"], [1, 2]),
            ([" peildatum ", "PERIODE"], [1, 2]),
            (["1", "2"], [1, 2]),
        ],
    )
    def test_measure_resource_normalizes_temporaltype_labels_case_insensitive(self, temporaltype_values, expected):
        dataset = Dataset()
        dataset.headers = ["name", "temporaltype"]

        for index, temporaltype_value in enumerate(temporaltype_values, start=1):
            dataset.append([f"MEASURE_{index}", temporaltype_value])

        resource = MeasureResource()
        resource.before_import(dataset)

        assert list(dataset["temporaltype"]) == expected

    def test_measure_resource_normalizes_deprecated_date_in_place(self):
        dataset = Dataset()
        dataset.headers = ["name", "deprecated_date"]
        dataset.append(["MEASURE_1", "2026-07-21"])

        resource = MeasureResource()
        resource.before_import(dataset)

        assert list(dataset["deprecated_date"]) == [date(2026, 7, 21)]

    def test_measure_resource_import_updates_existing_measure_when_name_not_uppercase(self):
        unit = baker.make("referentie_tabellen.Unit", name="aantal")
        measure = baker.make(
            Measure,
            name="EXISTING_MEASURE",
            label="Old label",
            definition="Old definition",
            unit=unit,
            team=baker.make("auth.Group"),
        )

        dataset = Dataset()
        dataset.headers = ["name", "label", "definition", "unit"]
        dataset.append(["existing_measure", "New label", "New definition", unit.name])

        resource = MeasureResource()
        result = resource.import_data(dataset, dry_run=False, raise_errors=False)

        assert result.has_errors() is False
        assert Measure.objects.count() == 1

        measure.refresh_from_db()
        assert measure.label == "New label"
        assert measure.definition == "New definition"

    def test_measure_resource_rejects_non_deprecated_columns_for_deprecated_measure(self):
        unit = baker.make("referentie_tabellen.Unit", name="aantal")
        measure = baker.make(
            Measure,
            name="DEPRECATED_MEASURE",
            label="Old label",
            definition="Old definition",
            unit=unit,
            team=baker.make(Group),
            deprecated=True,
        )

        dataset = Dataset()
        dataset.headers = ["name", "label"]
        dataset.append([measure.name, "New label"])

        resource = MeasureResource()

        with pytest.raises(ValueError) as exc_info:
            resource.before_import(dataset)

        assert "mogen niet geimporteerd worden" in str(exc_info.value)
        assert measure.name in str(exc_info.value)

    def test_measure_resource_rejects_deprecated_columns_for_deprecated_measure(self):
        unit = baker.make("referentie_tabellen.Unit", name="aantal")
        measure = baker.make(
            Measure,
            name="DEPRECATED_MEASURE",
            unit=unit,
            team=baker.make(Group),
            deprecated=True,
            deprecated_reason="Old reason",
        )

        dataset = Dataset()
        dataset.headers = ["name", "deprecated_reason"]
        dataset.append([measure.name.lower(), "New reason"])

        resource = MeasureResource()
        with pytest.raises(ValueError) as exc_info:
            resource.before_import(dataset)

        assert "mogen niet geimporteerd worden" in str(exc_info.value)
        assert measure.name in str(exc_info.value)

    def test_measure_resource_allows_setting_existing_active_measure_to_deprecated(self):
        unit = baker.make("referentie_tabellen.Unit", name="aantal")
        measure = baker.make(
            Measure,
            name="ACTIVE_MEASURE",
            unit=unit,
            team=baker.make(Group),
            deprecated=False,
        )

        dataset = Dataset()
        dataset.headers = ["name", "deprecated", "deprecated_reason"]
        dataset.append([measure.name.lower(), True, "No longer used"])

        resource = MeasureResource()
        result = resource.import_data(dataset, dry_run=False, raise_errors=False)

        assert result.has_errors() is False
        assert result.has_validation_errors() is False

        measure.refresh_from_db()
        assert measure.deprecated is True
        assert measure.deprecated_reason == "No longer used"
