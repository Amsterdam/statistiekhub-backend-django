# Generated by Django 4.1.13 on 2024-05-10 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PublicationMeasure",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, unique=True)),
                ("label", models.CharField(max_length=75)),
                ("label_uk", models.CharField(blank=True, max_length=75, null=True)),
                ("definition", models.TextField()),
                ("definition_uk", models.TextField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("source", models.CharField(max_length=100)),
                ("theme", models.CharField(max_length=50)),
                ("theme_uk", models.CharField(max_length=50)),
                ("unit", models.CharField(max_length=30)),
                ("unit_code", models.CharField(blank=True, max_length=5, null=True)),
                ("unit_symbol", models.CharField(blank=True, max_length=15, null=True)),
                ("decimals", models.IntegerField()),
                ("sensitive", models.BooleanField()),
                ("parent", models.CharField(blank=True, max_length=50, null=True)),
                ("extra_attr", models.JSONField(blank=True, null=True)),
                ("deprecated", models.BooleanField()),
                ("deprecated_date", models.DateField(blank=True, null=True)),
                ("deprecated_reason", models.TextField(blank=True, null=True)),
                ("calculation", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="PublicationObservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("spatialdimensiontype", models.CharField(max_length=50)),
                ("spatialdimensiondate", models.DateField()),
                ("spatialdimensioncode", models.CharField(max_length=100)),
                (
                    "spatialdimensionname",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("temporaldimensiontype", models.CharField(max_length=50)),
                ("temporaldimensionstartdate", models.DateField()),
                ("temporaldimensionenddate", models.DateField()),
                ("temporaldimensionyear", models.PositiveIntegerField()),
                ("measure", models.CharField(max_length=50)),
                ("value", models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="PublicationStatistic",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("spatialdimensiondate", models.DateField()),
                ("temporaldimensiontype", models.CharField(max_length=50)),
                ("temporaldimensionstartdate", models.DateField()),
                ("temporaldimensionyear", models.PositiveIntegerField()),
                ("measure", models.CharField(max_length=50)),
                ("average", models.DecimalField(decimal_places=3, max_digits=19)),
                (
                    "standarddeviation",
                    models.DecimalField(decimal_places=3, max_digits=19),
                ),
                ("source", models.CharField(max_length=100)),
            ],
        ),
    ]
