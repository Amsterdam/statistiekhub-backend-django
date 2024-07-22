from django.core.exceptions import ValidationError
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from referentie_tabellen.models import TemporalDimensionType
from statistiek_hub.models.temporal_dimension import TemporalDimension
from statistiek_hub.utils.check_functions import check_missing_fields
from statistiek_hub.utils.datetime import convert_to_date


class TemporalDimensionResource(ModelResource):
    type = Field(
        column_name="type",
        attribute="type",
        widget=ForeignKeyWidget(TemporalDimensionType, field="name"),
    )

    def before_import(self, dataset, **kwargs):
        # check column_names importfile
        expected = ["type", "startdate"]

        error = check_missing_fields(fields=dataset.headers, expected=expected)
        if error:
            # to speed validation -> if errors empty dataset so no row's will be checked
            del dataset[0 : len(dataset)]
            raise ValidationError(error)

        # omzetten naar datum veld
        dataset.append_col(
            tuple([convert_to_date(x) for x in dataset["startdate"]]),
            header="startdate",
        )

    class Meta:
        model = TemporalDimension
        exclude = ("id",)
        import_id_fields = ("type", "startdate")
