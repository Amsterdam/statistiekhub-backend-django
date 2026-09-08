from django.db import migrations

from publicatie_tabellen.db_functions.function_calculate_observations import (
    function_calculate_observation,
)


class Migration(migrations.Migration):
    dependencies = [
        ("publicatie_tabellen", "0011_alter_publicationmeasure_theme_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=function_calculate_observation,
            reverse_sql=(
                "DROP FUNCTION IF EXISTS public.calculate_observation(integer, character varying);"
            ),
        )
    ]
