from django.db import migrations, models


def forward_update_ou_to_oi(apps, schema_editor):
    FreightCost = apps.get_model("bom", "FreightCost")
    FreightCost.objects.filter(burden_type="OU BURDEN").update(
        burden_type="OI BURDEN"
    )


def backward_update_oi_to_ou(apps, schema_editor):
    FreightCost = apps.get_model("bom", "FreightCost")
    FreightCost.objects.filter(burden_type="OI BURDEN").update(
        burden_type="OU BURDEN"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0015_update_oi_burden_to_ou"),
    ]

    operations = [
        migrations.RunPython(forward_update_ou_to_oi, backward_update_oi_to_ou),
        migrations.AlterField(
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