import django.contrib.postgres.fields
from django.db import migrations, models
from statistiek_hub.utils.truncate_model import truncate


def truncate_publicationmeasure(apps, schema_editor):
    PublicationMeasure = apps.get_model("publicatie_tabellen", "PublicationMeasure")
    truncate(PublicationMeasure)


class Migration(migrations.Migration):
    dependencies = [
        ("publicatie_tabellen", "0007_publicationobservation_measure_idx"),
    ]

    operations = [
        migrations.RunPython(truncate_publicationmeasure, reverse_code=migrations.RunPython.noop),

        migrations.AlterField(
            model_name='publicationmeasure',
            name='theme',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), default=list),
        ),
        migrations.AlterField(
            model_name='publicationmeasure',
            name='theme_uk',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), default=list),
        ),
    ]