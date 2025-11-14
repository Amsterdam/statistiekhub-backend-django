import django.db.models.deletion
from django.db import migrations, models


def add_theme_to_groups(apps, schema_editor):
    """Forward: Add prefix to groups that don't have it"""
    Theme = apps.get_model("referentie_tabellen", "Theme")
    Group = apps.get_model("auth", "Group")

    # This gets the current model definition, not the historical one
    from referentie_tabellen.models import Theme as CurrentTheme

    group_prefix = CurrentTheme.group_prefix

    # Find all unique groups used by themes that don't start with the prefix
    theme_groups = (
        Theme.objects.filter(group__isnull=False)
        .exclude(group__name__startswith=group_prefix)
        .values_list("group_id", flat=True)
        .distinct()
    )

    groups_to_update = Group.objects.filter(id__in=theme_groups)

    for group in groups_to_update:
        group.name = f"{group_prefix}{group.name}"
        group.save()


def remove_theme_from_groups(apps, schema_editor):
    """Reverse: No need to remove the prefix from groups"""


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("referentie_tabellen", "0003_source"),
    ]

    operations = [
        migrations.RunPython(
            add_theme_to_groups,
            remove_theme_from_groups,
        ),
        migrations.AlterField(
            model_name="theme",
            name="group",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"name__startswith": "theme_"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="auth.group",
            ),
        ),
    ]
