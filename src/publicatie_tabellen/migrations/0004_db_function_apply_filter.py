# Generated by Django 4.1.2 on 2023-02-07 16:21

from django.db import migrations

from publicatie_tabellen.db_functions.function_apply_filter import function_apply_filter


class Migration(migrations.Migration):
    dependencies = [
        ("publicatie_tabellen", "0003_publicationupdatedat"),     
    ]

    operations = [
            migrations.RunSQL(function_apply_filter, ('DROP FUNCTION public.apply_filter;')),
    ]