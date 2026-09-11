from django.db import migrations, models


BACKFILL_BATCH_SIZE = 1000


def backfill_freightcostdetail_fields(apps, schema_editor):
    FreightCostDetail = apps.get_model("bom", "FreightCostDetail")
    fields_to_update = [
        "item_code",
        "item_description",
        "from_location",
        "to_location",
        "expedition_name",
        "expedition_type",
        "kode_cab",
        "nama_cab",
    ]

    pending_updates = []
    queryset = FreightCostDetail.objects.select_related(
        "freight__location", "freight__expedition"
    )

    for detail in queryset.iterator(chunk_size=BACKFILL_BATCH_SIZE):
        changed = False
        freight = detail.freight
        location = freight.location if freight else None
        expedition = freight.expedition if freight else None

        if not (detail.item_code or "").strip():
            detail.item_code = detail.name or ""
            changed = True

        if not (detail.item_description or "").strip():
            detail.item_description = detail.description or ""
            changed = True

        if location:
            location_values = {
                "from_location": location.from_location or location.name or "",
                "to_location": location.to_location or location.description or "",
                "kode_cab": location.kode_cab or "",
                "nama_cab": location.nama_cab or location.name or "",
            }
            for field_name, value in location_values.items():
                if not (getattr(detail, field_name) or "").strip() and value:
                    setattr(detail, field_name, value)
                    changed = True

        if expedition:
            expedition_values = {
                "expedition_name": expedition.name or "",
                "expedition_type": expedition.expedition_type or "",
            }
            for field_name, value in expedition_values.items():
                if not (getattr(detail, field_name) or "").strip() and value:
                    setattr(detail, field_name, value)
                    changed = True

        if changed:
            pending_updates.append(detail)

        if len(pending_updates) >= BACKFILL_BATCH_SIZE:
            FreightCostDetail.objects.bulk_update(pending_updates, fields_to_update)
            pending_updates = []

    if pending_updates:
        FreightCostDetail.objects.bulk_update(pending_updates, fields_to_update)


class Migration(migrations.Migration):

    dependencies = [
        ("bom", "0017_remove_duplicate_constraint_from_freightcostdetail"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="freightcostdetail",
            options={
                "db_table": "bom_freightcost_detail",
                "ordering": ["freight", "item_code", "id"],
                "permissions": [
                    ("soft_delete", "Can delete items"),
                    ("soft_restore", "Can restore deleted items"),
                ],
                "verbose_name": "Freight Cost Detail",
                "verbose_name_plural": "Freight Cost Details",
            },
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="expedition_name",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                null=True,
                verbose_name="Expedition Name",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="expedition_type",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                null=True,
                verbose_name="Expedition Type",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="from_location",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                null=True,
                verbose_name="From Location",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="item_code",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                null=True,
                verbose_name="Item Code",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="item_description",
            field=models.CharField(
                blank=True,
                default="",
                max_length=255,
                null=True,
                verbose_name="Item Description",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="kode_cab",
            field=models.CharField(
                blank=True,
                default="",
                max_length=20,
                null=True,
                verbose_name="Kode Cabang",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="nama_cab",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                null=True,
                verbose_name="Nama Cabang",
            ),
        ),
        migrations.AddField(
            model_name="freightcostdetail",
            name="to_location",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                null=True,
                verbose_name="To Location",
            ),
        ),
        migrations.RunPython(
            backfill_freightcostdetail_fields,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="freightcost",
            name="expedition",
        ),
        migrations.RemoveField(
            model_name="freightcost",
            name="location",
        ),
        migrations.DeleteModel(
            name="FreightCostExpedition",
        ),
        migrations.DeleteModel(
            name="FreightCostLocation",
        ),
    ]