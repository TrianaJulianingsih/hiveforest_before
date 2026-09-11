from django.db import migrations, models


def forward_update_oi_to_ou(apps, schema_editor):
    FreightCost = apps.get_model("bom", "FreightCost")
    FreightCost.objects.filter(burden_type="OI BURDEN").update(
        burden_type="OU BURDEN"
    )


def backward_update_ou_to_oi(apps, schema_editor):
    FreightCost = apps.get_model("bom", "FreightCost")
    FreightCost.objects.filter(burden_type="OU BURDEN").update(
        burden_type="OI BURDEN"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0014_add_case_insensitive_unique_constraint_to_freightcostdetail"),
    ]

    operations = [
        migrations.RunPython(forward_update_oi_to_ou, backward_update_ou_to_oi),
        migrations.AlterField(
            model_name="freightcost",
            name="burden_type",
            field=models.CharField(
                choices=[("OU BURDEN", "OU BURDEN"), ("MUP BURDEN", "MUP BURDEN")],
                default="OU BURDEN",
                max_length=20,
                verbose_name="Burden Type",
            ),
        ),
    ]