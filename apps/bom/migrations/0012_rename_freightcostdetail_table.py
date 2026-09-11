from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0011_add_product_distributor_to_freightcostdetail"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="freightcostdetail",
            table="bom_freightcost_detail",
        ),
    ]