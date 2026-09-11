from django.db import migrations

RESET_SQL = (
    "SELECT setval(pg_get_serial_sequence('auth_permission','id'), "
    "COALESCE((SELECT MAX(id) FROM auth_permission), 1), true);"
)

class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0024_fix_contenttypes_sequence'),
    ]

    operations = [
        migrations.RunSQL(sql=RESET_SQL, reverse_sql=''),
    ]
