from django.db import migrations


def sync_item_group_from_product_subgroup(apps, schema_editor):
    FreightCostDetail = apps.get_model("bom", "FreightCostDetail")

    for detail in FreightCostDetail.objects.select_related("product", "product__subgroup", "product__packaging").all():
        if not detail.product_id:
            continue

        detail.packaging_type_id = detail.product.packaging_id
        detail.item_group = detail.product.subgroup.name if detail.product.subgroup_id else ""
        detail.save(update_fields=["packaging_type", "item_group"])


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0007_sync_freight_detail_product_fields"),
    ]

    operations = [
        migrations.RunPython(sync_item_group_from_product_subgroup, migrations.RunPython.noop),
    ]
