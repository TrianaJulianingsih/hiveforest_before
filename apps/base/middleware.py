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
