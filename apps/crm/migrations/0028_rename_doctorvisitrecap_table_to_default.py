from django.db import migrations


def rename_to_default(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    vendor = schema_editor.connection.vendor
    bas_table = 'bas_rekap_kunjungan_by_dokter'
    default_table = 'crm_doctorvisitrecap'

    def table_exists(name):
        if vendor == 'postgresql':
            cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name=%s;", [name])
            return cursor.fetchone() is not None
        elif vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", [name])
            return cursor.fetchone() is not None
        elif vendor == 'mysql':
            cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name=%s;", [name])
            return cursor.fetchone() is not None
        else:
            try:
                cursor.execute(f"SELECT 1 FROM {name} LIMIT 1")
                return True
            except Exception:
                return False

    try:
        bas_exists = table_exists(bas_table)
        default_exists = table_exists(default_table)
        # If legacy name exists and default does not, rename legacy to default
        if bas_exists and not default_exists:
            if vendor == 'mysql':
                cursor.execute(f"RENAME TABLE {bas_table} TO {default_table};")
            else:
                cursor.execute(f"ALTER TABLE {bas_table} RENAME TO {default_table};")
    finally:
        cursor.close()


def reverse_rename_to_default(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    vendor = schema_editor.connection.vendor
    bas_table = 'bas_rekap_kunjungan_by_dokter'
    default_table = 'crm_doctorvisitrecap'

    def table_exists(name):
        if vendor == 'postgresql':
            cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name=%s;", [name])
            return cursor.fetchone() is not None
        elif vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", [name])
            return cursor.fetchone() is not None
        elif vendor == 'mysql':
            cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name=%s;", [name])
            return cursor.fetchone() is not None
        else:
            try:
                cursor.execute(f"SELECT 1 FROM {name} LIMIT 1")
                return True
            except Exception:
                return False

    try:
        bas_exists = table_exists(bas_table)
        default_exists = table_exists(default_table)
        # Reverse: if default exists and legacy does not, rename default back to legacy
        if default_exists and not bas_exists:
            if vendor == 'mysql':
                cursor.execute(f"RENAME TABLE {default_table} TO {bas_table};")
            else:
                cursor.execute(f"ALTER TABLE {default_table} RENAME TO {bas_table};")
    finally:
        cursor.close()


class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0027_recreate_doctorvisitrecap_table'),
    ]

    operations = [
        migrations.RunPython(rename_to_default, reverse_rename_to_default),
    ]
