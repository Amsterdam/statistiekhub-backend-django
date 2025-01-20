import pandas as pd


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


def set_stringfields_to_upper(df: pd.DataFrame) -> pd.DataFrame:
    """ set all stringfields in the dataframe to upper"""
    df = df.map(lambda x: x.upper() if isinstance(x, str) else x)
    return df