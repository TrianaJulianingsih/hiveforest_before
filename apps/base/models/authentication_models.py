import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.base.models.abstracts import GenericAbstract


class AuthenticationMethod(models.TextChoices):
    LOCAL = "local", _("Local")
    MICROSOFT = "microsoft", _("Microsoft Entra ID")


class AuthenticationResult(models.TextChoices):
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    LOGOUT = "logout", _("Logout")


class AuthenticationSetting(GenericAbstract):
    enable_local_login = models.BooleanField(default=True)
    enable_microsoft_login = models.BooleanField(default=False)
    require_mfa = models.BooleanField(default=False)
    auto_create_user = models.BooleanField(default=True)
    auto_update_user = models.BooleanField(default=True)
    allowed_email_domains = models.TextField(
        blank=True,
        default="",
        help_text=_("Separate multiple domains with commas or new lines."),
    )
    default_user_is_active = models.BooleanField(default=True)
    default_user_is_staff = models.BooleanField(default=False)
    default_user_is_superuser = models.BooleanField(default=False)
    login_button_text = models.CharField(
        max_length=100,
        default="Sign in with Microsoft",
    )
    login_message = models.CharField(
        max_length=255,
        default="Sign in to start your session",
    )
    enable_login_log = models.BooleanField(default=True)
    enable_logout_log = models.BooleanField(default=True)
    enable_failed_login_log = models.BooleanField(default=True)

    class Meta:
        db_table = "base_authentication"
        verbose_name = "Authentication Management"
        verbose_name_plural = "Authentication Management"

    def __str__(self):
        return "Authentication Management"

    def clean(self):
        super().clean()
        if not self.enable_local_login and not self.enable_microsoft_login:
            raise ValidationError(
                _("At least one authentication provider must remain enabled.")
            )

    def save(self, *args, **kwargs):
        self.pk = 1
        self.name = self.name or "Authentication Management"
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "name": "Authentication Management",
                "allowed_email_domains": os.environ.get("ALLOWED_DOMAIN", ""),
            },
        )
        return obj

    @property
    def allowed_domain_list(self):
        raw_domains = self.allowed_email_domains.replace("\r", "\n").replace(",", "\n")
        domains = [item.strip().lower() for item in raw_domains.split("\n") if item.strip()]
        return list(dict.fromkeys(domains))


class UserAuthentication(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authentication_profile",
    )
    authentication_enabled = models.BooleanField(default=True)
    allow_local_login = models.BooleanField(default=True)
    allow_microsoft_login = models.BooleanField(default=True)
    require_mfa = models.BooleanField(
        default=False,
        help_text=_("Require authenticator code after username and password."),
    )
    authenticator_secret = models.CharField(max_length=64, blank=True, default="")
    authenticator_confirmed = models.BooleanField(default=False)
    authenticator_last_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "base_user_authentication"
        verbose_name = "User Authentication Setup"
        verbose_name_plural = "User Authentication Setup"
        ordering = ("user__username",)

    def __str__(self):
        return f"{self.user.username}"


class AuthenticationLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authentication_logs",
    )
    username = models.CharField(max_length=150, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    browser = models.CharField(max_length=100, blank=True, default="")
    operating_system = models.CharField(max_length=100, blank=True, default="")
    login_method = models.CharField(
        max_length=20,
        choices=AuthenticationMethod.choices,
    )
    login_result = models.CharField(
        max_length=20,
        choices=AuthenticationResult.choices,
    )
    failure_reason = models.CharField(max_length=255, blank=True, default="")
    session_key = models.CharField(max_length=64, blank=True, default="")
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "base_authentication_log"
        verbose_name = "Authentication Log"
        verbose_name_plural = "Authentication Logs"
        ordering = ("-login_time",)
        indexes = [
            models.Index(fields=("login_time",)),
            models.Index(fields=("login_method", "login_result")),
            models.Index(fields=("user", "login_time")),
        ]

    def __str__(self):
        identity = self.user.username if self.user else self.username or "anonymous"
        return f"{identity} - {self.login_method} - {self.login_result}"
