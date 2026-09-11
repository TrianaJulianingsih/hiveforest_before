from django.db import migrations


def repair_django_content_type(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # Nothing to repair on a freshly-created table: modern Django/Postgres
        # creates "id" as a proper IDENTITY column, which Postgres refuses to
        # manually re-own below. This repair only applies to older databases
        # whose id sequence got detached from the column.
        cursor.execute(
            "SELECT is_identity FROM information_schema.columns "
            "WHERE table_name = 'django_content_type' AND column_name = 'id'"
        )
        row = cursor.fetchone()
        if row and row[0] == "YES":
            return

        cursor.execute("SELECT to_regclass('public.django_content_type_id_seq')")
        if cursor.fetchone()[0] is None:
            cursor.execute("CREATE SEQUENCE django_content_type_id_seq")

        cursor.execute(
            "SELECT setval('django_content_type_id_seq', "
            "COALESCE((SELECT MAX(id) FROM django_content_type WHERE id IS NOT NULL), 1), true)"
        )
        cursor.execute(
            "UPDATE django_content_type "
            "SET id = nextval('django_content_type_id_seq') "
            "WHERE id IS NULL"
        )
        cursor.execute(
            "SELECT setval('django_content_type_id_seq', "
            "COALESCE((SELECT MAX(id) FROM django_content_type), 1), true)"
        )

        cursor.execute(
            "ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id"
        )
        cursor.execute(
            "ALTER TABLE django_content_type "
            "ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq')"
        )
        cursor.execute(
            "ALTER TABLE django_content_type ALTER COLUMN id SET NOT NULL"
        )
        cursor.execute(
            "ALTER TABLE django_content_type ALTER COLUMN app_label SET NOT NULL"
        )
        cursor.execute(
            "ALTER TABLE django_content_type ALTER COLUMN model SET NOT NULL"
        )

        cursor.execute(
            "SELECT 1 "
            "FROM pg_constraint c "
            "JOIN pg_class t ON c.conrelid = t.oid "
            "WHERE t.relname = 'django_content_type' AND c.contype = 'p'"
        )
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE django_content_type ADD PRIMARY KEY (id)")

        cursor.execute(
            "SELECT 1 "
            "FROM pg_constraint c "
            "JOIN pg_class t ON c.conrelid = t.oid "
            "WHERE t.relname = 'django_content_type' "
            "AND c.conname = 'django_content_type_app_label_model_76bd3d3b_uniq'"
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "ALTER TABLE django_content_type "
                "ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq "
                "UNIQUE (app_label, model)"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("base", "0099_merge_20260504_1538"),
    ]

    operations = [
        migrations.RunPython(
            repair_django_content_type,
            reverse_code=migrations.RunPython.noop,
        ),
    ]