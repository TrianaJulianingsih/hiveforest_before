from django.db import migrations


def sync_freight_detail_product_fields(apps, schema_editor):
    FreightCostDetail = apps.get_model("bom", "FreightCostDetail")

    for detail in FreightCostDetail.objects.select_related("product", "product__packaging").all():
        if not detail.product_id:
            continue

        detail.packaging_type_id = detail.product.packaging_id
        detail.item_group = str(detail.product.subgroup_id or "")
        detail.save(update_fields=["packaging_type", "item_group"])


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0006_resync_freight_location_code_from_regency_iso"),
    ]

    operations = [
        migrations.RunPython(sync_freight_detail_product_fields, migrations.RunPython.noop),
    ]
