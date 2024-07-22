from pandas import DataFrame
from tablib import Dataset


def check_exists_in_model(
    dataset: Dataset, dfmodel: DataFrame, column: list, field: list
):
    """check if values from import (dataset[column]) exists in a model field

    Return
    -----------
    if value not exists in model:
    Returned: self made error with information on not_found
    if value exists:
    Returned: False (=no error)
    """

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


def check_missing_fields(fields: list, expected: list):
    """check if all expected items exist in fields

    Returns
    ----------
    if not all expected items exist in fields:
    Returned: error message with missings
    if all exists:
    Returned: false
    """

    # check list items
    _diff = set(expected) - set(fields)

    if _diff:
        error = f"Missing column(s) {list(_diff)}. Mandatory fields are: {expected}"
    else:
        error = False
    return error
