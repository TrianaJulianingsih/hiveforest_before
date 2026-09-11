from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0012_rename_freightcostdetail_table"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="freightcost",
            constraint=models.UniqueConstraint(
                Lower("name"),
                condition=~Q(name=""),
                name="uniq_bom_freightcost_name_ci",
            ),
        ),
    ]