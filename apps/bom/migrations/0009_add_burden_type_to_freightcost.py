from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0008_sync_item_group_from_product_subgroup"),
    ]

    operations = [
        migrations.AddField(
            model_name="freightcost",
            name="burden_type",
            field=models.CharField(
                choices=[("OI BURDEN", "OI BURDEN"), ("MUP BURDEN", "MUP BURDEN")],
                default="OI BURDEN",
                max_length=20,
                verbose_name="Burden Type",
            ),
        ),
    ]
