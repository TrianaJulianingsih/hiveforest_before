from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0016_update_ou_burden_to_oi"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="freightcostdetail",
            name="uniq_bom_freightcost_detail_item_ci",
        ),
    ]