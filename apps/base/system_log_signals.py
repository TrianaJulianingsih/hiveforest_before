from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from apps.base.services.system_log_service import SystemLogService, sanitize_payload
from apps.base.models.system_log import LogAction, LogStatus

@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    SystemLogService.log(
        request=request,
        user=user,
        action=LogAction.LOGIN,
        module="Authentication",
        feature="Login",
        description=f"User '{user.username}' successfully logged in.",
        status=LogStatus.SUCCESS,
        log_type="AUTHENTICATION"
    )

@receiver(user_logged_out)
def log_user_logged_out(sender, request, user, **kwargs):
    if user:
        SystemLogService.log(
            request=request,
            user=user,
            action=LogAction.LOGOUT,
            module="Authentication",
            feature="Logout",
            description=f"User '{user.username}' logged out.",
            status=LogStatus.SUCCESS,
            log_type="AUTHENTICATION"
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', '')
    SystemLogService.log(
        request=request,
        action=LogAction.LOGIN,
        module="Authentication",
        feature="Login",
        description=f"Invalid login attempt for username: '{username}'",
        status=LogStatus.ERROR,
        metadata={"credentials": sanitize_payload(credentials)},
        log_type="AUTHENTICATION"
    )
