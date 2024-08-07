# Generated by Django 4.1.13 on 2024-04-26 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("statistiek_hub", "0004_temporaldimension_duplicate_tempdim_constraint"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="observation",
            constraint=models.UniqueConstraint(
                fields=("measure", "spatialdimension", "temporaldimension"),
                name="duplicate_observation_constraint",
            ),
        ),
        migrations.AddConstraint(
            model_name="observationcalculated",
            constraint=models.UniqueConstraint(
                fields=("measure", "spatialdimension", "temporaldimension"),
                name="duplicate_calc_observation_constraint",
            ),
        ),
        migrations.AddConstraint(
            model_name="spatialdimension",
            constraint=models.UniqueConstraint(
                fields=("code", "type", "source_date"),
                name="duplicate_specdim_constraint",
            ),
        ),
    ]
