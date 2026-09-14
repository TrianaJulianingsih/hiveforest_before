from django.conf import settings
from django.db import migrations, models


def add_or_rename_user_column(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='humancapital_employee'"
        )
        columns = [row[0] for row in cursor.fetchall()]

    if 'id_user_id' in columns:
        schema_editor.execute(
            "ALTER TABLE humancapital_employee RENAME COLUMN id_user_id TO user_id;"
        )
    elif 'user_id' not in columns:
        Employee = apps.get_model('humancapital', 'Employee')
        User = apps.get_model('auth', 'User')
        field = models.OneToOneField(
            User,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='employee',
            verbose_name='User',
            db_column='user_id',
        )
        field.contribute_to_class(Employee, 'user')
        schema_editor.add_field(Employee, field)


class Migration(migrations.Migration):

    dependencies = [
        ("humancapital", "0035_assignment_site"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(add_or_rename_user_column, reverse_code=migrations.RunPython.noop),
    ]

