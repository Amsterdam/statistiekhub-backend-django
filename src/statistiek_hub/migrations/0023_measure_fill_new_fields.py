from django.db import migrations


def migrate_fields_from_extraattr_to_new_fields(apps, schema_editor):
    Measure = apps.get_model("statistiek_hub", "Measure")
    field_map = {
        "BBGA_verschijningsfrequentie": "frequency",
        "BBGA_frequency": "frequency_uk",
        "BBGA_labelkort": "label_short",
        "BBGA_label_1": "label_short_uk",
    }

    queryset = Measure.objects.exclude(extra_attr__isnull=True)
    for measure in queryset.iterator():
        extra_attr = measure.extra_attr or {}
        update_fields = set()

        # Copy json values into the new CharFields (only if empty).
        for json_key, model_field in field_map.items():
            if json_key not in extra_attr:
                continue

            value = extra_attr.get(json_key)
            if value is not None and not getattr(measure, model_field):
                setattr(measure, model_field, str(value)[:40])  # Slice to fit max_length
                update_fields.add(model_field)

            # Remove migrated (or redundant) keys from extra_attr.
            extra_attr.pop(json_key, None)
            update_fields.add("extra_attr")

        if update_fields:
            measure.extra_attr = extra_attr or None
            measure.save(update_fields=list(update_fields))


class Migration(migrations.Migration):
    dependencies = [
        ("statistiek_hub", "0022_measure_description_uk_measure_frequency_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_fields_from_extraattr_to_new_fields),
    ]
