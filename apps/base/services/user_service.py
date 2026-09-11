from django.contrib.auth import get_user_model

from apps.base.models.authentication_models import UserAuthentication
from apps.base.services.setting_service import get_authentication_setting


User = get_user_model()


def get_or_create_user_authentication(user):
    return UserAuthentication.objects.get_or_create(
        user=user,
        defaults={
            "authentication_enabled": True,
            "allow_local_login": True,
            "allow_microsoft_login": True,
        },
    )[0]


def apply_default_flags(user):
    setting = get_authentication_setting()
    user.is_active = setting.default_user_is_active
    user.is_staff = setting.default_user_is_staff
    user.is_superuser = setting.default_user_is_superuser
    return user


def build_username_from_claims(claims):
    email = (
        claims.get("preferred_username")
        or claims.get("email")
        or claims.get("upn")
        or ""
    ).strip().lower()
    return email


def update_user_from_claims(user, claims):
    user.first_name = (claims.get("given_name") or user.first_name or "").strip()
    user.last_name = (claims.get("family_name") or user.last_name or "").strip()
    user.email = (
        claims.get("email")
        or claims.get("preferred_username")
        or user.email
        or ""
    ).strip().lower()
    return user
