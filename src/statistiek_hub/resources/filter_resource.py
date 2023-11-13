from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from statistiek_hub.models.filter import Filter
from statistiek_hub.models.measure import Measure
from statistiek_hub.utils.check_import_fields import check_missing_import_fields
from statistiek_hub.utils.resource_checkPK import SimpleError


class FilterResource(ModelResource):
    measure = Field(
        column_name="measure",
        attribute="measure",
        widget=ForeignKeyWidget(Measure, field="name"),
    )

    basemeasure = Field(
        column_name="basemeasure",
        attribute="basemeasure",
        widget=ForeignKeyWidget(Measure, field="name"),
    )

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        # check main error's first on Dataset (instead of row by row)

        print(dataset.headers)
        print(dataset[0:10])

        errors = {}

        # check column_names importfile
        expected = [
            "measure",
            "basemeasure",
            "lessthan",
            "value_new",
        ]

        error = check_missing_import_fields(fields=dataset.headers, expected=expected )
        if error:
            errors["column_names"] = error
        else:
            #     # check measure_names exist
            #     error = check_exists_in_model(dataset=dataset, model=Measure, column="measure", field="name")
            #     if error:
            #         errors["measure_names"] = error

            #     # check basemeasure_names exist
            #     error = check_exists_in_model(dataset=dataset, model=Measure, column="basemeasure", field="name")
            #     if error:
            #         errors["basemeasure_names"] = error

            # if errors:
            #     # to speed validation -> if errors empty dataset so no row's will be checked
            #     del dataset[0 : len(dataset)]
            #     raise ValidationError(errors)
            pass

    @classmethod
    def get_error_result_class(self):
        """
        Returns a class which has custom formatting of the error.
        Used here to simplify the trace error
        """
        return SimpleError

    class Meta:
        model = Filter
        skip_unchanged = True
        report_skipped = True
        exclude = ("id",)
        fields = ("measure", "basemeasure", "lessthan", "value_new")
        import_id_fields = ("measure", "basemeasure")
