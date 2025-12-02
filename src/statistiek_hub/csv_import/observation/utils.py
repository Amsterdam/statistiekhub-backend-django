import pandas as pd
from django.db.backends.utils import CursorWrapper


def execute_query_and_return_dataframe(
    query: str,
    cursor: CursorWrapper,
) -> pd.DataFrame:
    cursor.execute(query)

    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=column_names)
