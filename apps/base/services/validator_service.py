from django.core.exceptions import PermissionDenied


class AuthenticationDeniedError(PermissionDenied):
    pass


def validate_email_domain(email, allowed_domains):
    if not allowed_domains:
        return

    normalized_email = (email or "").strip().lower()
    if "@" not in normalized_email:
        raise AuthenticationDeniedError("Email domain is required for this login.")

    domain = normalized_email.rsplit("@", 1)[1]
    if domain not in allowed_domains:
        raise AuthenticationDeniedError("Email domain is not allowed.")


def validate_user_is_enabled(user_authentication):
    if user_authentication and not user_authentication.authentication_enabled:
        raise AuthenticationDeniedError("Authentication is disabled for this user.")
