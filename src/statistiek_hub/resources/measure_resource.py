from django.contrib.auth.models import Group
from import_export.fields import Field
from import_export.instance_loaders import CachedInstanceLoader
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from referentie_tabellen.models import Source, Theme, Unit
from statistiek_hub.models.dimension import Dimension
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.datetime import convert_to_date
from statistiek_hub.validations import get_instance

MANYTOMANY_SEPARATOR = "|"


class InstanceForeignKeyWidget(ForeignKeyWidget):
    def __init__(
        self,
        model,
        field="pk",
        *,
        column_name: str,
        required: bool = True,
        **kwargs,
    ):
        super().__init__(model=model, field=field, **kwargs)
        self.column_name = column_name
        self.required = required

    def clean(self, value, row, **kwargs):
        raw_value = "" if value is None else str(value).strip()
        if raw_value == "":
            if self.required:
                raise ValueError(f"Kolom '{self.column_name}' is verplicht en mag niet leeg zijn.")
            return None

        instance, error = get_instance(model=self.model, field=self.field, value=raw_value, column=self.column_name)
        if error:
            raise ValueError(error)

        return instance


class RequiredManyToManyWidget(ManyToManyWidget):
    def __init__(
        self,
        model,
        field="pk",
        separator=MANYTOMANY_SEPARATOR,
        *,
        column_name: str,
        **kwargs,
    ):
        super().__init__(model=model, field=field, separator=separator, **kwargs)
        self.column_name = column_name

    def clean(self, value, row=None, *args, **kwargs):
        if value is None or str(value).strip() == "":
            raise ValueError(f"Kolom '{self.column_name}' is verplicht en mag niet leeg zijn.")

        values = [v.strip() for v in str(value).split(self.separator) if v.strip()]
        qs = self.model.objects.filter(**{f"{self.field}__in": values})
        found_values = set(qs.values_list(self.field, flat=True))
        missing_values = [v for v in values if v not in found_values]
        if missing_values:
            missing = ", ".join(missing_values)
            raise ValueError(f"De volgende waarde(n) in kolom '{self.column_name}' bestaan niet: {missing}.")

        return qs


class MeasureResource(ModelResource):
    unit = Field(
        column_name="unit",
        attribute="unit",
        widget=InstanceForeignKeyWidget(Unit, field="name", column_name="unit", required=True),
    )

    team = Field(
        column_name="team",
        attribute="team",
        widget=InstanceForeignKeyWidget(Group, field="name", column_name="team", required=True),
    )

    themes = Field(
        column_name="theme",
        attribute="themes",
        widget=RequiredManyToManyWidget(Theme, field="name", column_name="theme"),
    )

    sources = Field(
        column_name="source",
        attribute="sources",
        widget=RequiredManyToManyWidget(Source, field="name", column_name="source"),
    )

    dimension = Field(
        column_name="dimension",
        attribute="dimension",
        widget=InstanceForeignKeyWidget(Dimension, field="code", column_name="dimension", required=False),
    )

    parent = Field(
        column_name="parent",
        attribute="parent",
        widget=InstanceForeignKeyWidget(Measure, field="name", column_name="parent", required=False),
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
