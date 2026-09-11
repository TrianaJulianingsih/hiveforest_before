from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.cache import never_cache

from apps.base.models.authentication_models import AuthenticationMethod, AuthenticationResult
from apps.base.forms.authentication_forms import MFAVerificationForm
from apps.base.services.audit_service import log_authentication_attempt
from apps.base.services.authentication_service import get_login_context
from apps.base.services.user_service import get_or_create_user_authentication
from apps.base.utils.authentication_utils import (
    generate_authenticator_secret,
    get_authenticator_provisioning_uri,
    get_authenticator_qr_base64,
    is_mfa_required,
    validate_local_login,
    verify_totp_code,
)
from apps.base.services.validator_service import AuthenticationDeniedError


MFA_SESSION_USER_ID = "pending_mfa_user_id"
MFA_SESSION_BACKEND = "pending_mfa_backend"
MFA_SESSION_NEXT = "pending_mfa_next"


@method_decorator(never_cache, name="dispatch")
class AuthenticationLoginView(LoginView):
    template_name = "authentication_templates/login.html"
    redirect_authenticated_user = True
    _skip_invalid_audit = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_login_context())
        return context

    def form_valid(self, form):
        user = form.get_user()
        try:
            validate_local_login(self.request, user)
        except AuthenticationDeniedError as exc:
            form.add_error(None, str(exc))
            self._skip_invalid_audit = True
            log_authentication_attempt(
                self.request,
                user=user,
                username=user.username,
                method=AuthenticationMethod.LOCAL,
                result=AuthenticationResult.FAILED,
                failure_reason=str(exc),
            )
            return self.form_invalid(form)

        if is_mfa_required(user):
            user_auth = get_or_create_user_authentication(user)
            self.request.session[MFA_SESSION_USER_ID] = user.pk
            self.request.session[MFA_SESSION_BACKEND] = getattr(
                user,
                "backend",
                "django.contrib.auth.backends.ModelBackend",
            )
            self.request.session[MFA_SESSION_NEXT] = self.get_success_url()
            if not user_auth.authenticator_secret:
                user_auth.authenticator_secret = generate_authenticator_secret()
                user_auth.authenticator_confirmed = False
                user_auth.save(
                    update_fields=["authenticator_secret", "authenticator_confirmed", "updated_at"]
                )
            if not user_auth.authenticator_confirmed:
                return redirect("authentication_mfa_enroll")
            return redirect("authentication_mfa_verify")

        response = super().form_valid(form)
        log_authentication_attempt(
            self.request,
            user=user,
            username=user.username,
            method=AuthenticationMethod.LOCAL,
            result=AuthenticationResult.SUCCESS,
        )
        self.request.session["authentication_method"] = AuthenticationMethod.LOCAL
        return response

    def form_invalid(self, form):
        username = self.request.POST.get("username", "").strip()
        if username and not self._skip_invalid_audit:
            log_authentication_attempt(
                self.request,
                username=username,
                method=AuthenticationMethod.LOCAL,
                result=AuthenticationResult.FAILED,
                failure_reason="Invalid username or password.",
            )
        self._skip_invalid_audit = False
        return super().form_invalid(form)


@method_decorator(never_cache, name="dispatch")
class AuthenticationAdminLoginView(AuthenticationLoginView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            return render(request, "404.html", status=404)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(never_cache, name="dispatch")
class AuthenticationMFAVerifyView(FormView):
    template_name = "authentication_templates/mfa_verify.html"
    form_class = MFAVerificationForm

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get(MFA_SESSION_USER_ID):
            return redirect("login")
        user = self._get_pending_user()
        if not user:
            self._clear_pending_mfa_session()
            return redirect("login")
        user_auth = get_or_create_user_authentication(user)
        if not user_auth.authenticator_secret or not user_auth.authenticator_confirmed:
            return redirect("authentication_mfa_enroll")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_login_context())
        return context

    def form_valid(self, form):
        backend = self.request.session.get(MFA_SESSION_BACKEND, "django.contrib.auth.backends.ModelBackend")
        next_url = self.request.session.get(MFA_SESSION_NEXT) or self.get_success_url()
        user = self._get_pending_user()
        if not user:
            self._clear_pending_mfa_session()
            return redirect("login")

        user_auth = get_or_create_user_authentication(user)
        otp_code = form.cleaned_data["otp_code"]
        if not verify_totp_code(user_auth.authenticator_secret, otp_code):
            log_authentication_attempt(
                self.request,
                user=user,
                username=user.username,
                method=AuthenticationMethod.LOCAL,
                result=AuthenticationResult.FAILED,
                failure_reason="Invalid authenticator code.",
            )
            form.add_error("otp_code", "Invalid authenticator code.")
            return self.form_invalid(form)

        user_auth.authenticator_confirmed = True
        user_auth.authenticator_last_verified_at = timezone.now()
        user_auth.save(
            update_fields=["authenticator_confirmed", "authenticator_last_verified_at", "updated_at"]
        )
        login(self.request, user, backend=backend)
        self.request.session["authentication_method"] = AuthenticationMethod.LOCAL
        self._clear_pending_mfa_session()
        log_authentication_attempt(
            self.request,
            user=user,
            username=user.username,
            method=AuthenticationMethod.LOCAL,
            result=AuthenticationResult.SUCCESS,
        )
        return redirect(next_url)

    def _get_pending_user(self):
        from django.contrib.auth import get_user_model

        user_id = self.request.session.get(MFA_SESSION_USER_ID)
        return get_user_model().objects.filter(pk=user_id).first()

    def _clear_pending_mfa_session(self):
        for key in (MFA_SESSION_USER_ID, MFA_SESSION_BACKEND, MFA_SESSION_NEXT):
            self.request.session.pop(key, None)


@method_decorator(never_cache, name="dispatch")
class AuthenticationMFAEnrollView(FormView):
    template_name = "authentication_templates/mfa_enroll.html"
    form_class = MFAVerificationForm

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get(MFA_SESSION_USER_ID):
            return redirect("login")
        user = self._get_pending_user()
        if not user:
            self._clear_pending_mfa_session()
            return redirect("login")
        user_auth = get_or_create_user_authentication(user)
        if not user_auth.authenticator_secret:
            user_auth.authenticator_secret = generate_authenticator_secret()
            user_auth.save(update_fields=["authenticator_secret", "updated_at"])
        if user_auth.authenticator_confirmed:
            return redirect("authentication_mfa_verify")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self._get_pending_user()
        user_auth = get_or_create_user_authentication(user)
        context.update(get_login_context())
        context.update(
            {
                "authenticator_secret": user_auth.authenticator_secret,
                "authenticator_uri": get_authenticator_provisioning_uri(
                    user, user_auth.authenticator_secret
                ),
                "authenticator_qr_base64": get_authenticator_qr_base64(
                    user, user_auth.authenticator_secret
                ),
            }
        )
        return context

    def form_valid(self, form):
        user = self._get_pending_user()
        if not user:
            self._clear_pending_mfa_session()
            return redirect("login")

        user_auth = get_or_create_user_authentication(user)
        otp_code = form.cleaned_data["otp_code"]
        if not verify_totp_code(user_auth.authenticator_secret, otp_code):
            form.add_error("otp_code", "Invalid authenticator code.")
            log_authentication_attempt(
                self.request,
                user=user,
                username=user.username,
                method=AuthenticationMethod.LOCAL,
                result=AuthenticationResult.FAILED,
                failure_reason="Invalid authenticator enrollment code.",
            )
            return self.form_invalid(form)

        user_auth.authenticator_confirmed = True
        user_auth.authenticator_last_verified_at = timezone.now()
        user_auth.save(
            update_fields=["authenticator_confirmed", "authenticator_last_verified_at", "updated_at"]
        )
        return redirect("authentication_mfa_verify")

    def _get_pending_user(self):
        from django.contrib.auth import get_user_model

        user_id = self.request.session.get(MFA_SESSION_USER_ID)
        return get_user_model().objects.filter(pk=user_id).first()

    def _clear_pending_mfa_session(self):
        for key in (MFA_SESSION_USER_ID, MFA_SESSION_BACKEND, MFA_SESSION_NEXT):
            self.request.session.pop(key, None)


def authentication_provider_unavailable(request):
    messages.error(
        request,
        "Microsoft authentication package is not installed yet. Please contact the administrator.",
    )
    return HttpResponseForbidden("Microsoft authentication is unavailable.")
