import base64
import hashlib
import hmac
import io
import secrets
import struct
import time
from urllib.parse import quote

from importlib.util import find_spec

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied

from apps.base.models.authentication_models import (
    AuthenticationMethod,
    AuthenticationResult,
)
from apps.base.services.setting_service import get_authentication_setting
from apps.base.services.user_service import (
    apply_default_flags,
    build_username_from_claims,
    get_or_create_user_authentication,
    update_user_from_claims,
)
from apps.base.services.validator_service import (
    AuthenticationDeniedError,
    validate_email_domain,
    validate_user_is_enabled,
)


def get_client_ip(request):
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def parse_user_agent(user_agent):
    normalized = (user_agent or "").lower()
    browser = "Unknown"
    operating_system = "Unknown"

    browser_map = [
        ("edg/", "Edge"),
        ("chrome/", "Chrome"),
        ("firefox/", "Firefox"),
        ("safari/", "Safari"),
    ]
    for key, label in browser_map:
        if key in normalized:
            browser = label
            break

    os_map = [
        ("windows", "Windows"),
        ("iphone", "iOS"),
        ("ipad", "iOS"),
        ("android", "Android"),
        ("mac os", "macOS"),
        ("linux", "Linux"),
    ]
    for key, label in os_map:
        if key in normalized:
            operating_system = label
            break

    return browser, operating_system


def validate_local_login(request, user):
    setting = get_authentication_setting()
    user_auth = get_or_create_user_authentication(user)
    validate_user_is_enabled(user_auth)

    if not setting.enable_local_login or not user_auth.allow_local_login:
        raise AuthenticationDeniedError("Local login is disabled for this user.")

    validate_email_domain(user.email, setting.allowed_domain_list)

    return True


def generate_authenticator_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def get_totp_token(secret, for_time=None, interval=30, digits=6):
    timestamp = int(for_time or time.time())
    counter = timestamp // interval
    normalized_secret = (secret or "").strip().upper()
    padding = "=" * ((8 - len(normalized_secret) % 8) % 8)
    key = base64.b32decode(f"{normalized_secret}{padding}", casefold=True)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def verify_totp_code(secret, otp_code, valid_window=1):
    now = int(time.time())
    for offset in range(-valid_window, valid_window + 1):
        if get_totp_token(secret, for_time=now + (offset * 30)) == otp_code:
            return True
    return False


def is_mfa_required(user):
    setting = get_authentication_setting()
    user_auth = get_or_create_user_authentication(user)
    return bool(setting.require_mfa or user_auth.require_mfa)


def get_authenticator_provisioning_uri(user, secret, issuer=None):
    issuer_name = issuer or getattr(settings, "PROJECT_NAME", "HiveForest")
    account_name = getattr(user, "email", "") or getattr(user, "username", "")
    label = quote(f"{issuer_name}:{account_name}")
    issuer_qs = quote(issuer_name)
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer_qs}"


def get_authenticator_qr_base64(user, secret):
    try:
        import qrcode
    except ImportError:
        return ""

    image = qrcode.make(get_authenticator_provisioning_uri(user, secret))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


if find_spec("mozilla_django_oidc") is not None:
    from mozilla_django_oidc.auth import OIDCAuthenticationBackend

    class EntraIDOIDCAuthenticationBackend(OIDCAuthenticationBackend):
        def verify_claims(self, claims):
            from apps.base.services.audit_service import log_authentication_attempt

            setting = get_authentication_setting()
            if not setting.enable_microsoft_login:
                log_authentication_attempt(
                    self.request,
                    username=build_username_from_claims(claims),
                    method=AuthenticationMethod.MICROSOFT,
                    result=AuthenticationResult.FAILED,
                    failure_reason="Microsoft login is disabled.",
                )
                return False

            if not super().verify_claims(claims):
                log_authentication_attempt(
                    self.request,
                    username=build_username_from_claims(claims),
                    method=AuthenticationMethod.MICROSOFT,
                    result=AuthenticationResult.FAILED,
                    failure_reason="Token claim validation failed.",
                )
                return False

            email = (
                claims.get("email")
                or claims.get("preferred_username")
                or claims.get("upn")
                or ""
            ).strip().lower()

            try:
                validate_email_domain(email, setting.allowed_domain_list)
                self._protect_against_replay(claims)
            except PermissionDenied as exc:
                log_authentication_attempt(
                    self.request,
                    username=email,
                    method=AuthenticationMethod.MICROSOFT,
                    result=AuthenticationResult.FAILED,
                    failure_reason=str(exc),
                )
                return False

            return True

        def filter_users_by_claims(self, claims):
            email = (
                claims.get("email")
                or claims.get("preferred_username")
                or claims.get("upn")
                or ""
            ).strip().lower()
            username = build_username_from_claims(claims)
            model = get_user_model()
            queryset = model.objects.none()
            if email:
                queryset = model.objects.filter(email__iexact=email)
            if not queryset.exists() and username:
                queryset = model.objects.filter(username__iexact=username)
            return queryset

        def create_user(self, claims):
            setting = get_authentication_setting()
            if not setting.auto_create_user:
                raise PermissionDenied("Automatic user creation is disabled.")

            model = get_user_model()
            username = build_username_from_claims(claims)
            user = model(username=username)
            user = apply_default_flags(user)
            user = update_user_from_claims(user, claims)
            user.set_unusable_password()
            user.save()
            get_or_create_user_authentication(user)
            return user

        def update_user(self, user, claims):
            setting = get_authentication_setting()
            user_auth = get_or_create_user_authentication(user)
            validate_user_is_enabled(user_auth)
            if not user_auth.allow_microsoft_login:
                raise PermissionDenied("Microsoft login is disabled for this user.")

            if setting.auto_update_user:
                user = update_user_from_claims(user, claims)
                user.save(update_fields=["first_name", "last_name", "email"])
            return user

        def authenticate(self, request, **kwargs):
            from apps.base.services.audit_service import log_authentication_attempt

            user = super().authenticate(request, **kwargs)
            if user:
                if getattr(request, "session", None):
                    request.session["authentication_method"] = AuthenticationMethod.MICROSOFT
                log_authentication_attempt(
                    request,
                    user=user,
                    username=user.username,
                    method=AuthenticationMethod.MICROSOFT,
                    result=AuthenticationResult.SUCCESS,
                )
            return user

        def _protect_against_replay(self, claims):
            token_hash = "|".join(
                [
                    str(claims.get("sub", "")),
                    str(claims.get("iat", "")),
                    str(claims.get("nonce", "")),
                ]
            )
            if not token_hash.strip("||"):
                return
            cache_key = f"oidc-replay:{token_hash}"
            if cache.get(cache_key):
                raise PermissionDenied("Replay protection triggered.")
            cache.set(cache_key, True, timeout=settings.SESSION_COOKIE_AGE)
