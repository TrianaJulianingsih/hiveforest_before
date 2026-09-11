from django.utils import timezone

from apps.base.models.authentication_models import (
    AuthenticationLog,
    AuthenticationResult,
)
from apps.base.services.setting_service import get_authentication_setting
from apps.base.utils.authentication_utils import get_client_ip, parse_user_agent


def log_authentication_attempt(
    request,
    *,
    user=None,
    username="",
    method,
    result,
    failure_reason="",
):
    setting = get_authentication_setting()
    if result == AuthenticationResult.SUCCESS and not setting.enable_login_log:
        return None
    if result == AuthenticationResult.FAILED and not setting.enable_failed_login_log:
        return None
    if result == AuthenticationResult.LOGOUT and not setting.enable_logout_log:
        return None

    browser, operating_system = parse_user_agent(
        request.META.get("HTTP_USER_AGENT", "") if request else ""
    )
    session_key = ""
    if request and getattr(request, "session", None):
        session_key = request.session.session_key or ""

    return AuthenticationLog.objects.create(
        user=user,
        username=username or getattr(user, "username", ""),
        ip_address=get_client_ip(request) if request else None,
        browser=browser,
        operating_system=operating_system,
        login_method=method,
        login_result=result,
        failure_reason=failure_reason,
        session_key=session_key,
        login_time=timezone.now(),
        logout_time=timezone.now() if result == AuthenticationResult.LOGOUT else None,
    )


def mark_logout(request, user):
    setting = get_authentication_setting()
    if not setting.enable_logout_log:
        return

    session_key = ""
    if request and getattr(request, "session", None):
        session_key = request.session.session_key or ""
    method = "local"
    if request and getattr(request, "session", None):
        method = request.session.get("authentication_method", "local")

    log = (
        AuthenticationLog.objects.filter(
            user=user,
            session_key=session_key,
            logout_time__isnull=True,
        )
        .order_by("-login_time")
        .first()
    )
    if log:
        log.logout_time = timezone.now()
        log.save(update_fields=["logout_time"])
        return log

    return log_authentication_attempt(
        request,
        user=user,
        username=getattr(user, "username", ""),
        method=method,
        result=AuthenticationResult.LOGOUT,
    )
