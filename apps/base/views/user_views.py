from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from apps.base.forms import (
    CustomPasswordChangeForm,
    CustomSetPasswordForm,
    ForcePasswordChangeForm,
    build_password_policy_requirements,
)


def get_password_policy_context(user=None):
    from apps.base.models.password_policy import PasswordPolicy

    policy = PasswordPolicy.get_active_policy()
    return {
        "policy": policy,
        "requirements": build_password_policy_requirements(policy),
        "expiry_warning": (
            PasswordPolicy.get_password_expiry_warning(user)
            if user and policy
            else None
        ),
    }


def save_password_history(user, raw_password, changed_by):
    if not raw_password:
        return

    from apps.base.models.password_history import PasswordHistory
    from apps.base.models.password_policy import PasswordPolicy

    PasswordHistory.create_entry(user, raw_password, changed_by=changed_by)
    policy = PasswordPolicy.get_active_policy()
    if policy and policy.password_history_limit > 0:
        PasswordHistory.cleanup_old_entries(user, policy.password_history_limit)


class CustomPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = "registration/password_change_form.html"
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy("password_change_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_password_policy_context(self.request.user))
        return context

    def form_valid(self, form):
        raw_password = form.cleaned_data.get("new_password1")
        response = super().form_valid(form)

        save_password_history(self.request.user, raw_password, "user")

        from apps.base.user_models import ForcePasswordStatus

        status, _ = ForcePasswordStatus.objects.get_or_create(user=self.request.user)
        status.must_change_password = False
        status.last_reset_at = timezone.now()
        status.save()
        self.request.session["is_standard_password"] = False
        return response

    def form_invalid(self, form):
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return super().form_invalid(form)


# ═══════════════════════════════════════════════════════════
# FaisalS | Forgot Password function
# ═══════════════════════════════════════════════════════════
class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        self.request.session["reset_email"] = email
        return super().form_valid(form)


from apps.base.forms import CustomSetPasswordForm, ForcePasswordChangeForm


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("login")
    token_generator = default_token_generator
    form_class = CustomSetPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get("reset_email", "")
        context.update(
            get_password_policy_context(self.user if hasattr(self, "user") else None)
        )
        return context

    def form_valid(self, form):
        if "reset_email" in self.request.session:
            del self.request.session["reset_email"]
        self.request.session["reset_via_forgot"] = True

        user = form.save()

        raw_password = form.cleaned_data.get("new_password1")
        save_password_history(user, raw_password, "forgot_password")

        from apps.base.user_models import ForcePasswordStatus

        status, _ = ForcePasswordStatus.objects.get_or_create(user=user)
        status.must_change_password = False
        status.last_reset_at = timezone.now()
        status.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f" {error}")
        return super().form_invalid(form)

    def dispatch(self, *args, **kwargs):
        try:
            response = super().dispatch(*args, **kwargs)
            return response
        except Exception as e:
            messages.error(
                self.request,
                "An error occurred while processing your request. Please try again.",
            )
            return super().dispatch(*args, **kwargs)


# ═══════════════════════════════════════════════════════════
# // FaisalS | Forgot Password function
# ═══════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
#  FaisalS | Forced Password Change function
# ═══════════════════════════════════════════════════════════
class ForcePasswordChangeView(LoginRequiredMixin, View):
    template_name = "users/password_force_change.html"

    def _get_translations(self):
        """Get password change translations"""
        return {
            "force_change_title": "Forced Password Change",
            "force_change_subtitle": "You are required to change your password",
            "old_password_label": "Current Password",
            "new_password1_label": "New Password",
            "new_password1_help": "Your password must contain at least 8 characters.",
            "new_password2_label": "Confirm Password",
            "new_password2_help": "Enter the same password as before.",
            "password_requirements_title": "Password Requirements",
            "update_password_btn": "Update Password",
        }

    def get(self, request):
        form = ForcePasswordChangeForm(user=request.user)
        policy_context = get_password_policy_context(request.user)
        context = {
            "form": form,
            "requirements": policy_context["requirements"],
            "expiry_warning": policy_context["expiry_warning"],
            "t": self._get_translations(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = ForcePasswordChangeForm(user=request.user, data=request.POST)
        policy_context = get_password_policy_context(request.user)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get("new_password1")
            save_password_history(user, raw_password, "force_change")

            user.forcepasswordstatus.must_change_password = False
            user.forcepasswordstatus.last_reset_at = timezone.now()
            user.forcepasswordstatus.save()
            request.session["is_standard_password"] = False
            return redirect("login")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "requirements": policy_context["requirements"],
                "expiry_warning": policy_context["expiry_warning"],
                "t": self._get_translations(),
            },
        )


# ═══════════════════════════════════════════════════════════
#  // FaisalS | Forced Password Change function
# ═══════════════════════════════════════════════════════════
