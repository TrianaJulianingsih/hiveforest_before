from django.db import migrations

class Migration(migrations.Migration):
    # Run before 0001_initial to ensure the custom schema exists
    initial = True

    dependencies = []  # No dependencies; must run first

    operations = [
        migrations.RunSQL(
            sql="CREATE SCHEMA IF NOT EXISTS analytics;",
            reverse_sql="DROP SCHEMA IF EXISTS analytics CASCADE;"
        )
    ]
