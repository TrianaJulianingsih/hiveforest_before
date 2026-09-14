from datetime import timedelta
from django.utils import timezone, translation
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from apps.base.models.password_policy import PasswordPolicy
from .user_models import ForcePasswordStatus


class PersistLanguageMiddleware:
    """
    LocaleMiddleware activates a language for the current request (from the URL's
    own language prefix, the language cookie, or the Accept-Language header, in
    that order - Django 4+ no longer supports session-based language storage) but
    a URL-prefix-derived choice is never written back to the language cookie. Since
    the sidebar renders raw MenuItem.url hrefs with no language prefix
    (menu_tree.html/menu_recursive.html), clicking any menu item always
    re-resolves the language from the cookie/header, which was never updated - so
    navigation always fell back to the default language even right after switching
    to Indonesian on the page just visited. Writing whatever language actually got
    activated for this request into the cookie (the same mechanism
    django.views.i18n.set_language uses) keeps it "sticky" across links that don't
    carry an explicit prefix.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        active_language = translation.get_language()
        if active_language and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != active_language:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                active_language,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
        return response


# ═══════════════════════════════════════════════════════════
# FaisalS | Forgot Password function, Periodic Password Change function, Forced Password Change function
# ═══════════════════════════════════════════════════════════
class ForcePasswordChangeMiddleware:
    ALLOWED_PREFIXES = [
        "/static/",
        "/media/",
        "/admin/",
    ]

    EXEMPT_NAMES = ["password_force_change", "logout"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                force_url = reverse("password_force_change")
            except Exception:
                force_url = "/force-change/"

            path = request.path or ""
            if any(path.startswith(pfx) for pfx in self.ALLOWED_PREFIXES):
                return self.get_response(request)

            if not path.startswith(force_url):
                status, _ = ForcePasswordStatus.objects.get_or_create(user=request.user)

                is_standard = request.session.get("is_standard_password")
                if is_standard is None and not status.must_change_password:
                    is_standard = PasswordPolicy.check_user_has_standard_password(request.user)
                    request.session["is_standard_password"] = is_standard

                if is_standard and not status.must_change_password:
                    status.must_change_password = True
                    status.save()

                policy = PasswordPolicy.get_active_policy()
                expiry_days = (
                    policy.password_expiry_days
                    if policy and policy.password_expiry_days is not None
                    else settings.FORCE_PASSWORD_EXPIRY_DAYS
                )
                now_time = timezone.now()

                expired = False
                if expiry_days and expiry_days > 0:
                    expired = bool(
                        status.last_reset_at
                        and (
                            status.last_reset_at
                            < now_time - timedelta(days=expiry_days)
                        )
                    )

                if request.session.get("reset_via_forgot", False):
                    status.must_change_password = False
                    status.last_reset_at = now_time
                    status.save()
                    del request.session["reset_via_forgot"]
                else:
                    if status.must_change_password or expired:
                        if expired and not status.must_change_password:
                            status.must_change_password = True
                            status.save()
                        return redirect("password_force_change")

        return self.get_response(request)


import threading
import json
from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction, LogStatus

_thread_locals = threading.local()

class RequestProviderMiddleware:
    """Stores the active HTTP request object in a thread-local variable."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            if hasattr(_thread_locals, "request"):
                del _thread_locals.request
        return response

    @classmethod
    def get_current_request(cls):
        return getattr(_thread_locals, "request", None)


class SystemLogMiddleware:
    """Automatically logs REST API requests/responses and unhandled exceptions globally."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Check if the request is an API endpoint
        is_api = request.path.startswith('/api/')
        
        # 2. Extract API payload for POST, PUT, PATCH request methods
        payload = None
        if is_api and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    payload = json.loads(request.body)
                else:
                    payload = dict(request.POST)
            except Exception:
                pass

        response = self.get_response(request)

        # 3. Log API action details
        if is_api:
            resp_data = None
            if response.headers.get('Content-Type', '').startswith('application/json'):
                try:
                    resp_data = json.loads(response.content)
                except Exception:
                    pass

            status = LogStatus.SUCCESS if response.status_code < 400 else LogStatus.ERROR
            error_msg = None
            if status == LogStatus.ERROR:
                if resp_data:
                    error_msg = str(resp_data)
                else:
                    error_msg = f"HTTP {response.status_code} Error"

            feature_name = "API Endpoint"
            if request.resolver_match:
                feature_name = request.resolver_match.view_name

            SystemLogService.log(
                request=request,
                action=LogAction.API_REQUEST,
                module="API",
                feature=feature_name,
                description=f"API Request: {request.method} {request.path}",
                status=status,
                response_code=response.status_code,
                response_data=json.dumps(resp_data) if resp_data is not None else None,
                new_data=payload,
                error_message=error_msg,
                log_type="API"
            )

        return response

    def process_exception(self, request, exception):
        """Catches and logs unhandled exceptions thrown during request resolution."""
        import traceback
        tb = traceback.format_exc()
        
        feature_name = "Unhandled Exception"
        if request.resolver_match:
            feature_name = f"Exception in {request.resolver_match.view_name}"

        SystemLogService.error(
            request=request,
            module="System",
            feature=feature_name,
            error=exception,
            stack_trace=tb,
            log_type="SYSTEM"
        )
        return None

