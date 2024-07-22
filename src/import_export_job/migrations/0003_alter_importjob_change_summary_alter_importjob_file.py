# Generated by Django 5.0.7 on 2024-07-18 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("import_export_job", "0002_createcachetable"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importjob",
            name="change_summary",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="django-import-job-change-summaries",
                verbose_name="Summary of changes made by this import",
            ),
        ),
        migrations.AlterField(
            model_name="importjob",
            name="file",
            field=models.FileField(
                max_length=255,
                upload_to="django-import-jobs",
                verbose_name="File to be imported",
            ),
        ),
    ]
