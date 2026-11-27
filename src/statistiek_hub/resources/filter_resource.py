from django.core.exceptions import ValidationError
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.check_functions import (
    check_missing_fields,
)
from statistiek_hub.utils.converter import set_stringfields_to_upper


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
            # load dataset to pandas dataframe
            df_main = dataset.df
            df_main = set_stringfields_to_upper(df_main)

            imported_measure_names = {str(name).strip() for name in df_main["measure"] if str(name).strip()}
            existing_measures = list(
                Measure.objects.filter(name__in=imported_measure_names).values_list("name", "deprecated")
            )
            existing_measure_names = {name for name, _ in existing_measures}
            missing_measure_names = sorted(imported_measure_names - existing_measure_names)
            if missing_measure_names:
                missing_as_tuples = [(name,) for name in missing_measure_names]
                errors["measure_names"] = f"Niet terug gevonden in de referentietabel: {missing_as_tuples} "
            else:
                existing_deprecated_measure_names = {
                    name for name, deprecated in existing_measures if deprecated
                }
                if existing_deprecated_measure_names:
                    errors["measure_deprecated"] = (
                        "Filters voor vervallen variabelen mogen niet geimporteerd worden: "
                        f"{sorted(existing_deprecated_measure_names)}"
                    )

        if errors:
            # to speed validation -> if errors empty dataset so no row's will be checked
            del dataset[0 : len(dataset)]
            raise ValidationError(errors)

    class Meta:
        model = Filter
        clean_model_instances = True
        skip_unchanged = True
        report_skipped = True
        exclude = ("id",)
        fields = ("measure", "rule", "value_new")
        import_id_fields = ("measure",)
