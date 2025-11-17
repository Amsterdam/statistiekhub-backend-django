import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("referentie_tabellen", "0004_temporaldimensiontype_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="theme",
            name="group",
            field=models.ForeignKey(
                limit_choices_to=models.Q(
                    ("name__startswith", "modifier_"),
                    ("name__startswith", "maintainer"),
                    _connector="OR",
                    _negated=True,
                ),
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="auth.group",
            ),
        ),
    ]
