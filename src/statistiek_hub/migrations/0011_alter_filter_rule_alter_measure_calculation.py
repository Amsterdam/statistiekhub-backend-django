# Generated by Django 5.1.2 on 2024-11-22 15:48

import statistiek_hub.validations
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("statistiek_hub", "0010_remove_measure_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="filter",
            name="rule",
            field=models.TextField(
                validators=[statistiek_hub.validations.validate_filter_rule]
            ),
        ),
        migrations.AlterField(
            model_name="measure",
            name="calculation",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                validators=[statistiek_hub.validations.validate_calculation_string],
            ),
        ),
    ]
