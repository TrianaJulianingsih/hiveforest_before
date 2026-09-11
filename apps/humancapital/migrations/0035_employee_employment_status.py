from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('humancapital', '0034_alter_assignment_slug_alter_assignment_uat_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='employment_status',
            field=models.CharField(
                choices=[('regular', 'Regular'), ('probation', 'Probation')],
                default='regular',
                max_length=12,
                verbose_name='Employment status',
            ),
        ),
    ]
