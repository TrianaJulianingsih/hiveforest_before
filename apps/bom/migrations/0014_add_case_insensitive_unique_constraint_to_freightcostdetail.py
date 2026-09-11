from django.db import migrations, models
from django.db.models import Q, Value
from django.db.models.functions import Coalesce, Lower


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0013_add_case_insensitive_unique_constraint_to_freightcost"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="freightcostdetail",
            constraint=models.UniqueConstraint(
                "freight",
                Lower("name"),
                Lower(Coalesce("description", Value(""))),
                condition=Q(freight__isnull=False) & ~Q(name=""),
                name="uniq_bom_freightcost_detail_item_ci",
            ),
        ),
    ]