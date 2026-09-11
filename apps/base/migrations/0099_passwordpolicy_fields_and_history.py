# Migration to add password history fields to PasswordPolicy and create PasswordHistory table

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0098_passwordpolicy_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='passwordpolicy',
            name='password_history_limit',
            field=models.PositiveIntegerField(default=0, help_text='Number of previous passwords to maintain (0 = disabled)', verbose_name='Password History Limit'),
        ),
        migrations.AddField(
            model_name='passwordpolicy',
            name='check_password_history',
            field=models.BooleanField(default=False, help_text='Enable validation that previous passwords cannot be reused', verbose_name='Check Password History'),
        ),
        migrations.AddField(
            model_name='passwordpolicy',
            name='password_expiry_days',
            field=models.PositiveIntegerField(default=0, help_text='Number of days before password expires (0 = never expires)', verbose_name='Password Expiry Days'),
        ),
        migrations.AddField(
            model_name='passwordpolicy',
            name='password_expiry_warning_days',
            field=models.PositiveIntegerField(default=0, help_text='Show warning this many days before password expires', verbose_name='Password Expiry Warning Days'),
        ),
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password_hash', models.CharField(help_text='Hashed password for security', max_length=255, verbose_name='Password Hash')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date and time when password was changed', verbose_name='Created At')),
                ('changed_by', models.CharField(default='user', help_text="Who changed the password (e.g., 'user', 'admin', 'force_change')", max_length=50, verbose_name='Changed By')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_history', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Password History',
                'verbose_name_plural': 'Password Histories',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', '-created_at'], name='base_passwo_user_id_51da29_idx'), models.Index(fields=['user'], name='base_passwo_user_id_3c5c15_idx')],
            },
        ),
    ]
