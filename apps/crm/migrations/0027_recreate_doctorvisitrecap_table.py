from django.db import migrations


def create_table_if_missing(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    vendor = schema_editor.connection.vendor
    table_name = 'bas_rekap_kunjungan_by_dokter'

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
        if not table_exists(table_name):
            # Use Django's schema_editor to create the table from the current model state
            DoctorVisitRecap = apps.get_model('crm', 'DoctorVisitRecap')
            schema_editor.create_model(DoctorVisitRecap)
    finally:
        cursor.close()


def reverse_create_table_if_missing(apps, schema_editor):
    # No-op: we won't drop the table on reverse.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0026_alter_doctorvisitrecap_table'),
    ]

    operations = [
        migrations.RunPython(create_table_if_missing, reverse_create_table_if_missing),
    ]
