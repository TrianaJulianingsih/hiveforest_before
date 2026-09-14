from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0094_arearegencyhistory"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TerritoryAssignmentHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(blank=True, default="", max_length=30, verbose_name="Code")),
                ("name", models.CharField(blank=True, default="", max_length=255, verbose_name="Name")),
                ("action", models.CharField(choices=[("created", "Created"), ("updated", "Updated"), ("inactive", "Set Inactive")], max_length=20, verbose_name="Action")),
                ("changed_at", models.DateTimeField(auto_now_add=True, verbose_name="Changed At")),
                ("old_status", models.IntegerField(blank=True, null=True, verbose_name="Old Status")),
                ("new_status", models.IntegerField(blank=True, null=True, verbose_name="New Status")),
                ("old_effective", models.DateField(blank=True, null=True, verbose_name="Old Effective")),
                ("new_effective", models.DateField(blank=True, null=True, verbose_name="New Effective")),
                ("old_terminated", models.DateField(blank=True, null=True, verbose_name="Old Terminated")),
                ("new_terminated", models.DateField(blank=True, null=True, verbose_name="New Terminated")),
                ("remark", models.CharField(blank=True, max_length=255, null=True, verbose_name="Remark")),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="Changed By")),
                ("new_assignment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="territory_assignment_history_new_assignment", to="humancapital.assignment", verbose_name="New Assignment")),
                ("new_customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="territory_assignment_history_new_customer", to="sales.customer", verbose_name="New Customer")),
                ("old_assignment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="territory_assignment_history_old_assignment", to="humancapital.assignment", verbose_name="Old Assignment")),
                ("old_customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="territory_assignment_history_old_customer", to="sales.customer", verbose_name="Old Customer")),
                ("territory_assignment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="history_entries", to="sales.territoryassignment", verbose_name="Territory Assignment")),
            ],
            options={
                "verbose_name": "Territory Assignment History",
                "verbose_name_plural": "Territory Assignment Histories",
                "db_table": "sales_territory_assignment_history",
                "ordering": ["-changed_at"],
            },
        ),
    ]