from django.db import connection


def truncate(model):
    """
    truncate db table and restart AutoField primary_key for import

    use as follows:
    def before_import(self, dataset, **kwargs):
        # truncate table before import when dry_run = False
        if not dry_run:
            truncate(modelobject)
    """

    raw_query = f"""
        TRUNCATE TABLE {model._meta.db_table} RESTART IDENTITY
        """

    with connection.cursor() as cursor:
        cursor.execute(raw_query, {})
