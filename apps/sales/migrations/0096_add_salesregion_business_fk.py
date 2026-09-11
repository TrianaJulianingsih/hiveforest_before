# Generated migration to add missing FK constraint for sales_salesregion.business_id

from django.db import migrations, models
import django.db.models.deletion


def add_business_fk_constraint(apps, schema_editor):
    """Add FK constraint for business_id column if it doesn't already exist."""
    with schema_editor.connection.cursor() as cursor:
        # Check if the constraint already exists
        cursor.execute("""
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name='sales_salesregion'
            AND constraint_type='FOREIGN KEY'
            AND constraint_name LIKE '%business_id%'
        """)
        
        if not cursor.fetchone():
            # Constraint doesn't exist, add it
            cursor.execute("""
                ALTER TABLE sales_salesregion
                ADD CONSTRAINT sales_salesregion_business_id_fk
                FOREIGN KEY (business_id)
                REFERENCES humancapital_business(id)
                ON DELETE CASCADE
            """)


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0095_salesteam_business_to_humancapital_business"),
    ]

    operations = [
        migrations.RunPython(
            add_business_fk_constraint,
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
            ),
        ),
    ]
