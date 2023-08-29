from import_export.resources import Error


class SimpleError(Error):
    def __init__(self, error, traceback=None, row=None):
        super().__init__(error, traceback=traceback, row=row)
        self.traceback = ""


def check_exists_in_model(dataset, dfmodel, column: list, field: list):
    """check if values from import (dataset[column]) exists in a model field"""

    data_set = set(zip(*[list(str(x).upper() for x in dataset[c]) for c in column]))
    model_field = set(
        dfmodel[field]
        .astype(str)
        .apply(lambda col: col.str.upper())
        .apply(tuple, axis=1)
        .tolist()
    )

    if len(model_field) == 0:
        raise ValueError("check_exists_model gaat mis vanwege verkeerde argumenten?")

    not_found = [x for x in data_set if x not in model_field]

    if len(not_found) > 0:
        error = f"Niet terug gevonden in de referentietabel: {not_found} "
    else:
        error = False
    return error
