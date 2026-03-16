from django.contrib.auth.models import Group
from import_export.fields import Field
from import_export.instance_loaders import CachedInstanceLoader
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from referentie_tabellen.models import Theme, Unit
from statistiek_hub.models.dimension import Dimension
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.datetime import convert_to_date
from statistiek_hub.validations import get_instance

MANYTOMANY_SEPARATOR = "|"

class GroupForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        team, error = get_instance(model=Group, field="name", row=row, column="team")
        if error:
            raise ValueError(error)

        return team


class UnitForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        unit, error = get_instance(model=Unit, field="name", row=row, column="unit")
        if error:
            raise ValueError(error)

        return unit

   
class ThemeManyToManyWidget(ManyToManyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        if value is None or str(value).strip() == "":
            raise ValueError("Kolom 'theme' is verplicht en mag niet leeg zijn.")
        
        values = [v.strip() for v in value.split(MANYTOMANY_SEPARATOR) if v.strip()]
        qs = self.model.objects.filter(**{f"{self.field}__in": values})
        found_values = set(qs.values_list(self.field, flat=True))
        missing_values = [v for v in values if v not in found_values]
        if missing_values:
            missing = ", ".join(missing_values)
            raise ValueError(f"De volgende thema's bestaan niet: {missing}.")

        return qs


class DimensionForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        if row["dimension"]:
            dimension, error = get_instance(model=Dimension, field="code", row=row, column="dimension")
            if error:
                raise ValueError(error)

            return dimension


class ParentForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        if row["parent"]:
            parent, error = get_instance(model=Measure, field="name", row=row, column="parent")
            if error:
                raise ValueError(error)

            return parent


class MeasureResource(ModelResource):
    unit = Field(
        column_name="unit",
        attribute="unit",
        widget=UnitForeignKeyWidget(Unit, field="name"),
    )

    team = Field(
        column_name="team",
        attribute="team",
        widget=GroupForeignKeyWidget(Group, field="name"),
    )

    themes = Field(
        column_name="theme",
        attribute="themes",
        widget=ThemeManyToManyWidget(Theme, field="name"),
    )

    dimension = Field(
        column_name="dimension",
        attribute="dimension",
        widget=DimensionForeignKeyWidget(Dimension, field="code"),
    )

    parent = Field(
        column_name="parent",
        attribute="parent",
        widget=ParentForeignKeyWidget(Measure, field="name"),
    )

    def before_import(self, dataset, **kwargs):
        # keep track of headers so we only touch columns included in the file
        self._imported_headers = set(dataset.headers or [])

        if "name" not in self._imported_headers:
            raise ValueError("Importbestand mist de kolom 'name' om bestaande metingen te vinden.")

        if "deprecated_date" in self._imported_headers:
            # omzetten naar datum veld
            dataset.append_col(
                tuple(convert_to_date(x) for x in dataset["deprecated_date"]),
                header="deprecated_date",
            )

        return super().before_import(dataset, **kwargs)

    def import_field(self, field, instance, row, is_m2m=False, **kwargs):
        column_name = getattr(field, "column_name", None)
        if self._imported_headers and column_name and column_name not in self._imported_headers:
            return

        return super().import_field(field, instance, row, is_m2m=is_m2m, **kwargs)

    class Meta:
        model = Measure
        clean_model_instances = True
        skip_unchanged = True
        report_skipped = True
        exclude = ("id", "created_at", "updated_at")
        import_id_fields = ("name",)
        instance_loader_class = CachedInstanceLoader  # only works when there is one import_id_fields field
