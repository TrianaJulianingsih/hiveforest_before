from django.db import migrations, models


def populate_group_produk(apps, schema_editor):
    FreightCostDetail = apps.get_model("bom", "FreightCostDetail")

    for detail in FreightCostDetail.objects.select_related("product").all():
        if detail.group_produk:
            continue

        group_name = ""
        product = detail.product
        if product:
            distributor_items = product.distributoritem_set.select_related("group").all()
            for distributor_item in distributor_items:
                group = getattr(distributor_item, "group", None)
                if group and not getattr(group, "deleted", False):
                    group_name = group.name
                    break

        detail.group_produk = group_name
        detail.save(update_fields=["group_produk"])


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0009_add_burden_type_to_freightcost"),
    ]

    operations = [
        migrations.AddField(
            model_name="freightcostdetail",
            name="group_produk",
            field=models.CharField(blank=True, default="", max_length=100, null=True, verbose_name="Group Produk"),
        ),
        migrations.RunPython(populate_group_produk, migrations.RunPython.noop),
    ]
