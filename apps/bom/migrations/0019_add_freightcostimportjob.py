from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bom", "0018_align_freightcostdetail_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="FreightCostImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("upload_file", models.FileField(upload_to="freight_imports/")),
                ("original_filename", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="queued", max_length=20)),
                ("background_pid", models.IntegerField(blank=True, null=True)),
                ("total_rows", models.IntegerField(blank=True, null=True)),
                ("processed_rows", models.IntegerField(default=0)),
                ("created_rows", models.IntegerField(default=0)),
                ("skipped_rows", models.IntegerField(default=0)),
                ("chunk_count", models.IntegerField(default=0)),
                ("message", models.CharField(blank=True, default="", max_length=255)),
                ("error_message", models.TextField(blank=True, default="")),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="freight_cost_import_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Freight Cost Import Job",
                "verbose_name_plural": "Freight Cost Import Jobs",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]