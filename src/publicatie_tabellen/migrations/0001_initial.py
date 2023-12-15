# Generated by Django 4.1.13 on 2023-12-15 11:42

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PublicationMeasure",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=75, unique=True)),
                ("label", models.CharField(max_length=75)),
                ("label_uk", models.CharField(max_length=75)),
                ("definition", models.TextField()),
                ("definition_uk", models.TextField()),
                ("description", models.TextField(blank=True, null=True)),
                ("source", models.CharField(max_length=75)),
                ("theme", models.CharField(max_length=75)),
                ("theme_uk", models.CharField(max_length=75)),
                ("unit", models.CharField(max_length=75)),
                ("unit_code", models.CharField(max_length=75)),
                ("unit_symbol", models.CharField(max_length=75)),
                ("decimals", models.IntegerField()),
                ("sensitive", models.BooleanField()),
                ("parent", models.CharField(max_length=75)),
                ("extra_attr", models.JSONField()),
                ("deprecated", models.BooleanField()),
                ("deprecated_date", models.DateField()),
                ("deprecated_reason", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="PublicationObservation",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("spatialdimensiontype", models.CharField(max_length=75)),
                ("spatialdimensiondate", models.DateField(max_length=75)),
                ("spatialdimensioncode", models.CharField(max_length=75)),
                ("spatialdimensionname", models.CharField(max_length=75)),
                ("temporaldimensiontype", models.CharField(max_length=75)),
                ("temporaldimensionstartdate", models.DateTimeField()),
                ("temporaldimensionenddate", models.DateTimeField()),
                ("measure", models.CharField(max_length=75)),
                ("value", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="PublicationStatistic",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("spatialdimensiondate", models.DateField()),
                ("temporaldimensiontype", models.CharField(max_length=75)),
                ("temporaldimensionstartdate", models.DateTimeField()),
                ("measure", models.CharField(max_length=75)),
                ("average", models.FloatField()),
                ("standarddeviation", models.FloatField()),
                ("source", models.CharField(max_length=75)),
            ],
        ),
    ]
