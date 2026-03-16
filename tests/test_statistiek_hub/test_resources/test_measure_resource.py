import pytest
from model_bakery import baker

from referentie_tabellen.models import Theme
from statistiek_hub.resources.measure_resource import MANYTOMANY_SEPARATOR, ThemeManyToManyWidget


class TestThemeManyToManyWidget:
    def setup_method(self):
        self.widget = ThemeManyToManyWidget(Theme, field="name")

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

        assert missing_theme in str(exc.value)
