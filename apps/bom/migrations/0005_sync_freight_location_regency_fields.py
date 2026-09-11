from django.db import migrations


def sync_freight_location_regency_fields(apps, schema_editor):
    FreightCostLocation = apps.get_model("bom", "FreightCostLocation")

    for location in FreightCostLocation.objects.select_related("regency").all():
        if not location.regency_id:
            continue

        regency_name = (location.regency.name or "").strip()
        regency_iso = (location.regency.iso or "").strip()
        regency_code = (location.regency.code or "").strip()

        if regency_name:
            location.to_location = regency_name
            location.nama_cab = regency_name
        if regency_code:
            location.kode_cab = regency_code
        location.code = (regency_iso or regency_code or location.code or "")[:20]
        if not (location.name or "").strip():
            route_parts = [part for part in [location.from_location, regency_name] if part]
            location.name = " - ".join(route_parts) if route_parts else regency_name or location.code
        if not (location.description or "").strip():
            description_parts = [part for part in [location.from_location, regency_name] if part]
            location.description = " / ".join(description_parts)[:255] or None

        location.save(update_fields=[
            "to_location",
            "kode_cab",
            "nama_cab",
            "code",
            "name",
            "description",
        ])


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0004_restore_freightcostlocation_route_fields"),
    ]

    operations = [
        migrations.RunPython(sync_freight_location_regency_fields, migrations.RunPython.noop),
    ]
