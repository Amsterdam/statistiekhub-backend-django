# Generated by Django 5.1.1 on 2024-10-22 17:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("statistiek_hub", "0009_remove_filter_id_alter_filter_measure"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="measure",
            name="owner",
        ),
    ]
