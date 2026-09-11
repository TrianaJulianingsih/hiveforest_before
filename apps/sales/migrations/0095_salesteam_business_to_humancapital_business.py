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


def rename_salesteam_organization_to_business(apps, schema_editor):
    rename_column_if_needed(
        schema_editor,
        "sales_salesteam",
        "organization_id",
        "business_id",
    )


def rename_salesteam_business_to_organization(apps, schema_editor):
    rename_column_if_needed(
        schema_editor,
        "sales_salesteam",
        "business_id",
        "organization_id",
    )


def remap_salesteam_business_ids(apps, schema_editor):
    SalesTeam = apps.get_model("sales", "SalesTeam")

    SalesTeam.objects.exclude(business_id__in=[2, 3]).update(business_id=None)
    SalesTeam.objects.filter(business_id=2).update(business_id=1)
    SalesTeam.objects.filter(business_id=3).update(business_id=2)


class Migration(migrations.Migration):

    dependencies = [
        ("humancapital", "0035_business"),
        ("sales", "0094_business_fk_to_humancapital_business"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    rename_salesteam_organization_to_business,
                    reverse_code=rename_salesteam_business_to_organization,
                ),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name="salesteam",
                    old_name="organization",
                    new_name="business",
                ),
            ],
        ),
        migrations.RunPython(
            remap_salesteam_business_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="salesteam",
            name="business",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="humancapital.business",
                verbose_name="Business",
            ),
        ),
    ]