from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0101_alter_passwordpolicy_max_length_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthenticationSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="", max_length=100, verbose_name="Name")),
                ("description", models.CharField(blank=True, default="", max_length=255, null=True, verbose_name="Description")),
                ("remark", models.CharField(blank=True, max_length=255, null=True, verbose_name="Remark")),
                ("status", models.IntegerField(choices=[(1, "Active"), (0, "Inactive")], default=1, verbose_name="Status")),
                ("slug", models.SlugField(blank=True, default=None, max_length=255, null=True, unique=True, verbose_name="Slug")),
                ("cat", models.DateTimeField(auto_now_add=True, verbose_name="Created at")),
                ("uat", models.DateTimeField(blank=True, null=True, verbose_name="Updated at")),
                ("dat", models.DateTimeField(blank=True, null=True, verbose_name="Deleted at")),
                ("deleted", models.BooleanField(default=False)),
                ("enable_local_login", models.BooleanField(default=True)),
                ("enable_microsoft_login", models.BooleanField(default=False)),
                ("require_mfa", models.BooleanField(default=False)),
                ("auto_create_user", models.BooleanField(default=True)),
                ("auto_update_user", models.BooleanField(default=True)),
                ("allowed_email_domains", models.TextField(blank=True, default="", help_text="Separate multiple domains with commas or new lines.")),
                ("default_user_is_active", models.BooleanField(default=True)),
                ("default_user_is_staff", models.BooleanField(default=False)),
                ("default_user_is_superuser", models.BooleanField(default=False)),
                ("login_button_text", models.CharField(default="Sign in with Microsoft", max_length=100)),
                ("login_message", models.CharField(default="Sign in to start your session", max_length=255)),
                ("enable_login_log", models.BooleanField(default=True)),
                ("enable_logout_log", models.BooleanField(default=True)),
                ("enable_failed_login_log", models.BooleanField(default=True)),
                ("cby", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="Created by")),
                ("dby", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="authenticationsetting_deleted", to=settings.AUTH_USER_MODEL, verbose_name="Deleted by")),
                ("uby", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="authenticationsetting_updated", to=settings.AUTH_USER_MODEL, verbose_name="Updated by")),
            ],
            options={
                "verbose_name": "Authentication Management",
                "verbose_name_plural": "Authentication Management",
                "db_table": "base_authentication",
            },
        ),
        migrations.CreateModel(
            name="AuthenticationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(blank=True, default="", max_length=150)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("browser", models.CharField(blank=True, default="", max_length=100)),
                ("operating_system", models.CharField(blank=True, default="", max_length=100)),
                ("login_method", models.CharField(choices=[("local", "Local"), ("microsoft", "Microsoft Entra ID")], max_length=20)),
                ("login_result", models.CharField(choices=[("success", "Success"), ("failed", "Failed"), ("logout", "Logout")], max_length=20)),
                ("failure_reason", models.CharField(blank=True, default="", max_length=255)),
                ("session_key", models.CharField(blank=True, default="", max_length=64)),
                ("login_time", models.DateTimeField(default=django.utils.timezone.now)),
                ("logout_time", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="authentication_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Authentication Log",
                "verbose_name_plural": "Authentication Logs",
                "db_table": "base_authentication_log",
                "ordering": ("-login_time",),
            },
        ),
        migrations.CreateModel(
            name="UserAuthentication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("authentication_enabled", models.BooleanField(default=True)),
                ("allow_local_login", models.BooleanField(default=True)),
                ("allow_microsoft_login", models.BooleanField(default=True)),
                ("require_mfa", models.BooleanField(default=False, help_text="Require the user to authenticate through Microsoft when MFA is enforced.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="authentication_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "User Authentication Setup",
                "verbose_name_plural": "User Authentication Setup",
                "db_table": "base_user_authentication",
                "ordering": ("user__username",),
            },
        ),
        migrations.AddIndex(
            model_name="authenticationlog",
            index=models.Index(fields=["login_time"], name="base_authen_login_t_a1c619_idx"),
        ),
        migrations.AddIndex(
            model_name="authenticationlog",
            index=models.Index(fields=["login_method", "login_result"], name="base_authen_login_m_88e211_idx"),
        ),
        migrations.AddIndex(
            model_name="authenticationlog",
            index=models.Index(fields=["user", "login_time"], name="base_authen_user_id_8a8f95_idx"),
        ),
    ]
