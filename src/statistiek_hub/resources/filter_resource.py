import pandas as pd
from django.core.exceptions import ValidationError
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.check_functions import (
    check_exists_in_model,
    check_missing_fields,
)


class FilterResource(ModelResource):
    measure = Field(
        column_name="measure",
        attribute="measure",
        widget=ForeignKeyWidget(Measure, field="name"),
    )

    def before_import(self, dataset, **kwargs):
        # check main error's first on Dataset (instead of row by row)
        errors = {}

        # column_names importfile
        expected = [
            "measure",
            "rule",
            "value_new",
        ]

        error = check_missing_fields(fields=dataset.headers, expected=expected)
        if error:
            errors["column_names"] = error
        else:
            dfmeasure = pd.DataFrame(list(Measure.objects.values("id", "name")))
            error = check_exists_in_model(
                dataset=dataset, dfmodel=dfmeasure, column=["measure"], field=["name"]
            )

            if error:
                errors["measure_names"] = error
                
        if errors:
            # to speed validation -> if errors empty dataset so no row's will be checked
            del dataset[0 : len(dataset)]
            raise ValidationError(errors)


    class Meta:
        model = Filter
        skip_unchanged = True
        report_skipped = True
        exclude = ("id",)
        fields = ("measure", "rule", "value_new")
        import_id_fields = ("measure", "rule")
