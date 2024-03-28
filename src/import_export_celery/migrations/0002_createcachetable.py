from django.core.management import call_command
from django.db import migrations


def createcachetable(apps, schema_editor):
    call_command("createcachetable")


class Migration(migrations.Migration):
    dependencies = [
        ("import_export_celery", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(createcachetable),
    ]
