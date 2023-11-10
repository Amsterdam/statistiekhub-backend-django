
def check_missing_import_fields( fields: list, expected:list):
    """ returns 
            -error: if not all expected items exist in fields
            -false if all exist
    """

    # check list items
    list_a = fields
    list_b = expected

    _diff = list(set(list_b) - set(list_a)) 

    if len(_diff) > 0:
        error = f"Missing column(s) {_diff}. Mandatory fields are: {expected}"
    else:
        error = False
    return error