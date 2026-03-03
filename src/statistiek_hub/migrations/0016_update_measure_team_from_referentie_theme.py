from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("statistiek_hub", "0015_measure_team"),
        ("referentie_tabellen", "0005_alter_theme_group"),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE statistiek_hub_measure
            SET team_id = (
                SELECT referentie_tabellen_theme.group_id
                FROM referentie_tabellen_theme
                WHERE statistiek_hub_measure.theme_id = referentie_tabellen_theme.id
            )
            WHERE EXISTS (
                SELECT 1
                FROM referentie_tabellen_theme
                WHERE statistiek_hub_measure.theme_id = referentie_tabellen_theme.id
            );
            """,
            reverse_sql="""
            UPDATE statistiek_hub_measure
            SET team_id = NULL
            WHERE team_id IS NOT NULL;
            """,
        ),
    ]
