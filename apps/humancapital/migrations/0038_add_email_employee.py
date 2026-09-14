from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('humancapital', '0037_employee_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True, verbose_name='Email'),
        ),
    ]
