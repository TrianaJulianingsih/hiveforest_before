import django.db.models.deletion
from django.db import migrations, models


def rename_column_if_needed(schema_editor, table_name, old_column, new_column):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(cursor, table_name)

    columns = {column.name for column in description}
    if old_column in columns and new_column not in columns:
        schema_editor.execute(
            "ALTER TABLE {table} RENAME COLUMN {old} TO {new}".format(
                table=schema_editor.quote_name(table_name),
                old=schema_editor.quote_name(old_column),
                new=schema_editor.quote_name(new_column),
            )
        )


def rename_salesregion_organization_to_position(apps, schema_editor):
    rename_column_if_needed(
        schema_editor,
        "sales_salesregion",
        "organization_id",
        "position_id",
    )


def rename_salesregion_position_to_organization(apps, schema_editor):
    rename_column_if_needed(
        schema_editor,
        "sales_salesregion",
        "position_id",
        "organization_id",
    )


def update_salesregion_relations(apps, schema_editor):
    SalesRegion = apps.get_model("sales", "SalesRegion")

    SalesRegion.objects.exclude(position_id__isnull=True).update(position_id=None)

    SalesRegion.objects.filter(business_id=2).update(business_id=1)
    SalesRegion.objects.filter(business_id=3).update(business_id=2)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("humancapital", "0035_business"),
        ("sales", "0092_product_box_per_palletac"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    rename_salesregion_organization_to_position,
                    reverse_code=rename_salesregion_position_to_organization,
                ),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name="salesregion",
                    old_name="organization",
                    new_name="position",
                ),
            ],
        ),
        migrations.RunPython(
            update_salesregion_relations,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="salesregion",
            name="business",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="region_business",
                to="humancapital.business",
                verbose_name="Business",
            ),
        ),
        migrations.AlterField(
            model_name="salesregion",
            name="position",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="region_position",
                to="humancapital.position",
                verbose_name="Position",
            ),
        ),
    ]