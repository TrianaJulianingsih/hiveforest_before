from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("supplychain", "0035_stdistdaily_branch"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sales", "0092_product_box_per_palletac"),
    ]

    operations = [
        migrations.CreateModel(
            name="BranchStock",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="", max_length=100, verbose_name="Name")),
                ("description", models.CharField(blank=True, default="", max_length=255, null=True, verbose_name="Description")),
                ("remark", models.CharField(blank=True, max_length=255, null=True, verbose_name="Remark")),
                ("status", models.IntegerField(default=1, verbose_name="Status")),
                ("slug", models.SlugField(blank=True, default=None, max_length=255, null=True, unique=True, verbose_name="Slug")),
                ("cat", models.DateTimeField(auto_now_add=True, verbose_name="Created at")),
                ("uat", models.DateTimeField(blank=True, null=True, verbose_name="Updated at")),
                ("dat", models.DateTimeField(blank=True, null=True, verbose_name="Deleted at")),
                ("deleted", models.BooleanField(default=False)),
                ("product_name", models.CharField(help_text="Product label captured from stock source.", max_length=255, verbose_name="Product Name")),
                ("trx_date", models.DateField(verbose_name="Transaction Date")),
                ("total_reg", models.BigIntegerField(default=0, verbose_name="Total Reg")),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stock_summaries", to="supplychain.branch", verbose_name="Branch")),
                ("cby", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Created by")),
                ("dby", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="branchstock_deleted", to=settings.AUTH_USER_MODEL, verbose_name="Deleted by")),
                ("product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="branch_stock_entries", to="sales.product", verbose_name="Product")),
                ("team", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="branch_stock_entries", to="sales.productsubgroup", verbose_name="Team")),
                ("uby", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="branchstock_updated", to=settings.AUTH_USER_MODEL, verbose_name="Updated by")),
            ],
            options={
                "verbose_name": "Branch Stock",
                "verbose_name_plural": "Branch Stocks",
                "ordering": ("-trx_date", "branch__code", "product_name"),
            },
        ),
        migrations.AddConstraint(
            model_name="branchstock",
            constraint=models.UniqueConstraint(fields=("branch", "product_name", "trx_date"), name="supplychain_branchstock_unique_snapshot"),
        ),
        migrations.AddIndex(
            model_name="branchstock",
            index=models.Index(fields=("branch", "trx_date"), name="branchstock_branch_date_idx"),
        ),
        migrations.AddIndex(
            model_name="branchstock",
            index=models.Index(fields=("trx_date", "product_name"), name="branchstock_date_product_idx"),
        ),
    ]
