from django.db import migrations

RESET_SQL = (
    "SELECT setval(pg_get_serial_sequence('django_content_type','id'), "
    "COALESCE((SELECT MAX(id) FROM django_content_type), 1), true);"
)

class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0023_doctorvisitrecap'),
    ]

    operations = [
        migrations.RunSQL(sql=RESET_SQL, reverse_sql=''),
    ]
