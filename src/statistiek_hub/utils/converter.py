
def convert_str(value: str, to: str = "float"):
    """Convert string-value to format 'to'"""
    if "float" == to:
        # clean up if necessary
        value = value.replace(",", ".")

        if value  in ['NA', 'Null']:
            value = ''

        # convert to float
        try:
            value = float(value)
        finally:
            return value
    else:
        return value
