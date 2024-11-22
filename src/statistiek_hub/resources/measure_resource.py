from import_export.fields import Field
from import_export.instance_loaders import CachedInstanceLoader
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from referentie_tabellen.models import Theme, Unit
from statistiek_hub.models.dimension import Dimension
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.datetime import convert_to_date
from statistiek_hub.validations import get_instance


class UnitForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        unit, error = get_instance(model=Unit, field="name", row=row, column="unit")
        if error:
            raise ValueError(error)

        return unit


class ThemeForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        theme, error = get_instance(model=Theme, field="name", row=row, column="theme")
        if error:
            raise ValueError(error)

        return theme


class DimensionForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        if row["dimension"]:
            dimension, error = get_instance(
                model=Dimension, field="code", row=row, column="dimension"
            )
            if error:
                raise ValueError(error)

            return dimension


class ParentForeignKeyWidget(ForeignKeyWidget):
    def clean(self, value, row, **kwargs):
        if row["parent"]:
            parent, error = get_instance(
                model=Measure, field="name", row=row, column="parent"
            )
            if error:
                raise ValueError(error)

            return parent


class MeasureResource(ModelResource):
    unit = Field(
        column_name="unit",
        attribute="unit",
        widget=UnitForeignKeyWidget(Unit, field="name"),
    )

    theme = Field(
        column_name="theme",
        attribute="theme",
        widget=ThemeForeignKeyWidget(Theme, field="name"),
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
        # omzetten naar datum veld
        dataset.append_col(
            tuple([convert_to_date(x) for x in dataset["deprecated_date"]]),
            header="deprecated_date",
        )
        return super().before_import(dataset, **kwargs)

    class Meta:
        model = Measure
        clean_model_instances = True
        skip_unchanged = True
        report_skipped = True
        exclude = ("id", "created_at", "updated_at")
        import_id_fields = ("name",)
        use_bulk = True
        instance_loader_class = CachedInstanceLoader # only works when there is one import_id_fields field
