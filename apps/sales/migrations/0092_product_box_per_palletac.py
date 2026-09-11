from django.db import migrations, models


def add_box_per_palletac_if_missing(apps, schema_editor):
    product_model = apps.get_model("sales", "Product")
    table_name = product_model._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    if "box_per_palletac" in columns:
        return

    field = models.DecimalField(
        blank=True,
        null=True,
        verbose_name="Box / Pallet AC",
        max_digits=10,
        decimal_places=2,
    )
    field.set_attributes_from_name("box_per_palletac")
    field.model = product_model
    schema_editor.add_field(product_model, field)


def remove_box_per_palletac_if_present(apps, schema_editor):
    product_model = apps.get_model("sales", "Product")
    table_name = product_model._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    if "box_per_palletac" not in columns:
        return

    field = models.DecimalField(
        blank=True,
        null=True,
        verbose_name="Box / Pallet AC",
        max_digits=10,
        decimal_places=2,
    )
    field.set_attributes_from_name("box_per_palletac")
    field.model = product_model
    schema_editor.remove_field(product_model, field)


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0091_customer_subdist"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_box_per_palletac_if_missing,
                    reverse_code=remove_box_per_palletac_if_present,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="product",
                    name="box_per_palletac",
                    field=models.DecimalField(
                        blank=True,
                        null=True,
                        verbose_name="Box / Pallet AC",
                        max_digits=10,
                        decimal_places=2,
                    ),
                ),
            ],
        ),
    ]
