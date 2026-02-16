import pandas as pd

from statistiek_hub.utils.converter import set_stringfields_to_upper


def check_exists_in_model(dataset: pd.DataFrame, dfmodel: pd.DataFrame, column: list, field: list):
    """check if values from import (dataset[column]) exists in a model field

    Return
    -----------
    if value not exists in model:
    Returned: self made error with information on not_found
    if value exists:
    Returned: False (=no error)
    """

    data_set = set(dataset[column].astype(str).apply(lambda col: col.str.upper()).apply(tuple, axis=1).tolist())

    model_field = set(dfmodel[field].astype(str).apply(lambda col: col.str.upper()).apply(tuple, axis=1).tolist())

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


def check_temporaldimensiontype_observation_vs_measure(
    df_main: pd.DataFrame, dftemporaldim: pd.DataFrame, dfmeasure: pd.DataFrame
):
    df_main_nodup = set_stringfields_to_upper(df_main[["measure", "temporal_type"]].drop_duplicates())

    dftemporaldim_nodup = set_stringfields_to_upper(dftemporaldim[["type__name", "type__type"]].drop_duplicates())

    # join to get temporaldimensiontype.type on observation
    df_main_type = pd.merge(
        df_main_nodup,
        dftemporaldim_nodup,
        left_on="temporal_type",
        right_on="type__name",
        how="inner",
    )[["measure", "type__type"]]

    # join to compare with measure.temporaltype
    df_compare = pd.merge(
        df_main_type,
        dfmeasure[["name", "temporaltype"]],
        left_on="measure",
        right_on="name",
        how="inner",
    )

    # measures in observations that differ
    diff_df = df_compare[df_compare["type__type"] != df_compare["temporaltype"]]

    if len(diff_df) > 0:
        error = f"Measures {list(diff_df['measure'])} do not match their predefined temporaltype"
    else:
        error = False
    return error
