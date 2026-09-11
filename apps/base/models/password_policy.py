from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language


# ═══════════════════════════════════════════════════════════
# FaisalS | Password Policy
# ═══════════════════════════════════════════════════════════
def get_translated_message(key, default, params=None):
    try:
        from apps.base.models.translation import (
            TranslationKey,
            TranslationModule,
            Translation,
        )

        lang = get_language() or "en"
        module, _ = TranslationModule.objects.get_or_create(
            code="password_policy", defaults={"name": "Password Policy"}
        )
        tkey, _ = TranslationKey.objects.get_or_create(
            module=module, key=key, defaults={"default_value": default, "name": key}
        )
        trans = Translation.objects.filter(translation_key=tkey, language=lang).first()
        msg = trans.value if trans else default
        if params:
            return msg % params
        return msg
    except Exception:
        if params:
            return default % params
        return default


def get_standard_passwords():
    from django.conf import settings
    if hasattr(settings, "STANDARD_PASSWORDS") and settings.STANDARD_PASSWORDS:
        return set(settings.STANDARD_PASSWORDS)
    import os
    env_passwords = os.environ.get("STANDARD_PASSWORDS", "")
    if env_passwords:
        return {p.strip().lower() for p in env_passwords.split(",") if p.strip()}
    return {
        "password",
        "password1",
        "password123",
        "password123!",
        "p455w0rd",
        "p455w0rd!",
        "otsuka123",
        "otsuka123!",
        "otsuka@123",
        "12345678",
        "123456789",
        "qwerty",
        "letmein",
        "admin",
        "admin123",
        "welcome",
        "abc123",
        "hiveforest123",
        "hiveforest123!",
    }


class PasswordPolicy(models.Model):
    @classmethod
    def is_standard_password(cls, password):
        if not password:
            return False
        return password.lower() in get_standard_passwords()

    @classmethod
    def check_user_has_standard_password(cls, user, raw_password=None):
        if not user or not user.is_authenticated:
            return False
        standard_passwords = get_standard_passwords()
        if raw_password:
            return raw_password.lower() in standard_passwords
        for std_pass in standard_passwords:
            if user.check_password(std_pass):
                return True
        return False
    def _label(key, default):
        return get_translated_message(key, default)

    min_length = models.PositiveIntegerField(
        default=8, verbose_name=_("Minimum Password Length")
    )
    max_length = models.PositiveIntegerField(
        default=32, verbose_name=_("Maximum Password Length")
    )
    require_lowercase = models.BooleanField(
        default=False, verbose_name=_("Require Lowercase Letter")
    )
    require_uppercase = models.BooleanField(
        default=False, verbose_name=_("Require Uppercase Letter")
    )
    require_number = models.BooleanField(default=True, verbose_name=_("Require Number"))
    require_special = models.BooleanField(
        default=False, verbose_name=_("Require Special Character")
    )
    require_space = models.BooleanField(
        default=False, verbose_name=_("Require Space Character")
    )

    # Password History Settings
    password_history_limit = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Password History Limit"),
        help_text=_("Number of previous passwords to maintain (0 = disabled)"),
    )
    check_password_history = models.BooleanField(
        default=False,
        verbose_name=_("Check Password History"),
        help_text=_("Enable validation that previous passwords cannot be reused"),
    )

    # Password Expiry Settings
    password_expiry_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Password Expiry Days"),
        help_text=_("Number of days before password expires (0 = never expires)"),
    )
    password_expiry_warning_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Password Expiry Warning Days"),
        help_text=_("Show warning this many days before password expires"),
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Password Policy (min: {self.min_length}, max: {self.max_length}, "
            f"lowercase: {self.require_lowercase}, uppercase: {self.require_uppercase}, "
            f"number: {self.require_number}, special: {self.require_special}, "
            f"space: {self.require_space})"
        )

    class Meta:
        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")

    @classmethod
    def get_active_policy(cls):
        return cls.objects.first()

    @classmethod
    def validate_password(cls, password, user=None):
        policy = cls.get_active_policy()
        errors = []

        if cls.is_standard_password(password):
            errors.append(
                get_translated_message(
                    "standard_password_not_allowed_error",
                    "Password is a standard/default password and is not allowed. Please choose a unique password.",
                )
            )
        if password.isdigit():
            errors.append(
                get_translated_message(
                    "not_entirely_numeric_error",
                    "Password cannot be entirely numeric.",
                )
            )

        if not policy:
            return errors
        if len(password) < policy.min_length:
            errors.append(
                get_translated_message(
                    "min_length_error",
                    "Password must be at least %(min)d characters.",
                    {"min": policy.min_length},
                )
            )
        if policy.max_length and len(password) > policy.max_length:
            errors.append(
                get_translated_message(
                    "max_length_error",
                    "Password must be at most %(max)d characters.",
                    {"max": policy.max_length},
                )
            )
        if policy.require_lowercase and not any(c.islower() for c in password):
            errors.append(
                get_translated_message(
                    "require_lowercase_error",
                    "Password must contain a lowercase letter.",
                )
            )
        if policy.require_uppercase and not any(c.isupper() for c in password):
            errors.append(
                get_translated_message(
                    "require_uppercase_error",
                    "Password must contain an uppercase letter.",
                )
            )
        if policy.require_number and not any(c.isdigit() for c in password):
            errors.append(
                get_translated_message(
                    "require_number_error", "Password must contain a number."
                )
            )
        if policy.require_special and not any(
            not c.isalnum() and not c.isspace() for c in password
        ):
            errors.append(
                get_translated_message(
                    "require_special_error",
                    "Password must contain a special character.",
                )
            )
        if policy.require_space and not any(c.isspace() for c in password):
            errors.append(
                get_translated_message(
                    "require_space_error",
                    "Password must contain a space character.",
                )
            )
        if user:
            username = getattr(user, "username", None)
            email = getattr(user, "email", None)
            if username and username.lower() in password.lower():
                errors.append(
                    get_translated_message(
                        "not_too_similar_error",
                        "Password is too similar to your username.",
                    )
                )
            if email and email.split("@")[0].lower() in password.lower():
                errors.append(
                    get_translated_message(
                        "not_too_similar_error",
                        "Password is too similar to your email.",
                    )
                )
        return errors

    @classmethod
    def validate_password_history(cls, password, user):
        """Validate that password is not in user's password history"""
        policy = cls.get_active_policy()
        errors = []

        if (
            not policy
            or not policy.check_password_history
            or policy.password_history_limit == 0
        ):
            return errors

        # Import PasswordHistory here to avoid circular imports
        from apps.base.models.password_history import PasswordHistory

        # Get last N passwords from history
        history_entries = PasswordHistory.objects.filter(user=user).order_by(
            "-created_at"
        )[: policy.password_history_limit]

        for entry in history_entries:
            if entry.check_password(password):
                errors.append(
                    get_translated_message(
                        "password_in_history_error",
                        "This password was recently used. Please choose a different one.",
                    )
                )
                break

        return errors

    @classmethod
    def get_password_expiry_warning(cls, user):
        """Get password expiry warning for user (returns None if no warning needed)"""
        from django.utils import timezone
        from apps.base.user_models import ForcePasswordStatus
        from apps.base.models.password_history import PasswordHistory

        policy = cls.get_active_policy()
        if not policy or policy.password_expiry_days == 0:
            return None

        try:
            status = ForcePasswordStatus.objects.get(user=user)
            if not status.last_reset_at:
                return None

            # Get the most recent password change from history
            last_change = (
                PasswordHistory.objects.filter(user=user)
                .order_by("-created_at")
                .first()
            )
            password_change_date = (
                last_change.created_at if last_change else status.last_reset_at
            )

            expiry_date = password_change_date + timezone.timedelta(
                days=policy.password_expiry_days
            )
            days_until_expiry = (expiry_date - timezone.now()).days

            if days_until_expiry <= 0:
                return {
                    "expired": True,
                    "days_remaining": 0,
                    "expiry_date": expiry_date,
                }
            elif days_until_expiry <= policy.password_expiry_warning_days:
                return {
                    "expired": False,
                    "days_remaining": days_until_expiry,
                    "expiry_date": expiry_date,
                }
        except ForcePasswordStatus.DoesNotExist:
            pass

        return None
