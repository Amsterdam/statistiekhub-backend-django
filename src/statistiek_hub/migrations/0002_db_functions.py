# Generated by Django 4.1.2 on 2023-02-07 16:21

from django.db import migrations

from statistiek_hub.db_functions.function_apply_filter import function_apply_filter
from statistiek_hub.db_functions.function_calculate_observations import (
    function_calculate_observation,
)
from statistiek_hub.db_functions.function_round_observation import (
    function_round_observation,
)


class Migration(migrations.Migration):
    dependencies = [
        ("statistiek_hub", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(function_calculate_observation),
        migrations.RunSQL(function_round_observation),
        migrations.RunSQL(function_apply_filter),
    ]
