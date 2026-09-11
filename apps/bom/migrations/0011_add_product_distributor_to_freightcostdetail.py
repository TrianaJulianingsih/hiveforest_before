from django.db import migrations, models
import django.db.models.deletion


def populate_product_distributor(apps, schema_editor):
    FreightCostDetail = apps.get_model("bom", "FreightCostDetail")
    DistributorItem = apps.get_model("supplychain", "DistributorItem")

    distributor_by_code = {}
    distributor_by_name = {}
    distributor_by_product_id = {}

    for distributor_item in DistributorItem.objects.all().only(
        "id", "code", "name", "product_id"
    ):
        code_key = (distributor_item.code or "").strip().lower()
        name_key = (distributor_item.name or "").strip().lower()

        if code_key and code_key not in distributor_by_code:
            distributor_by_code[code_key] = distributor_item
        if name_key and name_key not in distributor_by_name:
            distributor_by_name[name_key] = distributor_item
        if distributor_item.product_id and distributor_item.product_id not in distributor_by_product_id:
            distributor_by_product_id[distributor_item.product_id] = distributor_item

    for detail in FreightCostDetail.objects.all().only(
        "id", "name", "description", "product_id", "product_distributor_id"
    ):
        if detail.product_distributor_id:
            continue

        distributor_item = None

        if detail.product_id:
            distributor_item = distributor_by_product_id.get(detail.product_id)

        if distributor_item is None:
            candidate_values = [detail.name, detail.description]
            for candidate in candidate_values:
                lookup_value = (candidate or "").strip().lower()
                if not lookup_value:
                    continue

                distributor_item = distributor_by_code.get(lookup_value) or distributor_by_name.get(
                    lookup_value
                )
                if distributor_item is not None:
                    break

        if distributor_item is None:
            continue

        update_fields = ["product_distributor"]
        detail.product_distributor_id = distributor_item.id

        if not detail.product_id and distributor_item.product_id:
            detail.product_id = distributor_item.product_id
            update_fields.append("product")

        detail.save(update_fields=update_fields)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("supplychain", "0036_stdistdaily_branch"),
        ("bom", "0010_add_group_produk_to_freightcostdetail"),
    ]

    operations = [
        migrations.AddField(
            model_name="freightcostdetail",
            name="product_distributor",
            field=models.ForeignKey(
                blank=True,
                db_column="product_id_distributor",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="freight_cost_details",
                to="supplychain.distributoritem",
                verbose_name="Product Distributor",
            ),
        ),
        migrations.RunPython(populate_product_distributor, migrations.RunPython.noop),
    ]