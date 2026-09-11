from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from apps.base.models.password_policy import get_translated_message
from django.utils.html import format_html, format_html_join


def build_password_policy_requirements(policy):
    requirements = []
    if not policy:
        return requirements

    if policy.min_length:
        requirements.append(
            get_translated_message(
                "min_length_error",
                _("Minimum %(min)d characters."),
                {"min": policy.min_length},
            )
        )
    if policy.max_length:
        requirements.append(
            get_translated_message(
                "max_length_error",
                _("Maximum %(max)d characters."),
                {"max": policy.max_length},
            )
        )
    if policy.require_lowercase:
        requirements.append(
            get_translated_message(
                "require_lowercase_error", _("Lowercase letter required.")
            )
        )
    if policy.require_uppercase:
        requirements.append(
            get_translated_message(
                "require_uppercase_error", _("Uppercase letter required.")
            )
        )
    if policy.require_number:
        requirements.append(
            get_translated_message("require_number_error", _("Number required."))
        )
    if policy.require_special:
        requirements.append(
            get_translated_message(
                "require_special_error", _("Special character required.")
            )
        )
    if policy.require_space:
        requirements.append(
            get_translated_message(
                "require_space_error", _("Space character required.")
            )
        )
    if policy.check_password_history and policy.password_history_limit > 0:
        requirements.append(
            get_translated_message(
                "password_history_info",
                _("Cannot reuse last %(count)d passwords."),
                {"count": policy.password_history_limit},
            )
        )
    if policy.password_expiry_days > 0:
        requirements.append(
            get_translated_message(
                "password_expiry_info",
                _("Password expires after %(days)d days."),
                {"days": policy.password_expiry_days},
            )
        )
    return requirements


def build_password_policy_help_text(policy):
    return ""


def validate_password_with_policy(password, user):
    from apps.base.models.password_policy import PasswordPolicy

    errors = PasswordPolicy.validate_password(password, user=user)
    errors.extend(PasswordPolicy.validate_password_history(password, user))
    return errors


# ═══════════════════════════════════════════════════════════
# FaisalS | Forced Password Change function
# ═══════════════════════════════════════════════════════════
class CustomSetPasswordForm(SetPasswordForm):
    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        errors = validate_password_with_policy(password, self.user)
        if errors:
            raise forms.ValidationError(errors)
        return password


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.base.models.password_policy import PasswordPolicy

        policy = PasswordPolicy.get_active_policy()
        self.fields["old_password"].label = get_translated_message(
            "old_password_label", _("Current password")
        )
        self.fields["new_password1"].label = get_translated_message(
            "new_password1_label", _("New password")
        )
        self.fields["new_password1"].help_text = build_password_policy_help_text(policy)
        self.fields["new_password2"].label = get_translated_message(
            "new_password2_label", _("Confirm new password")
        )
        self.fields["new_password2"].help_text = get_translated_message(
            "new_password2_help", _("Repeat your new password.")
        )

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        errors = validate_password_with_policy(password, self.user)
        if errors:
            raise forms.ValidationError(errors)
        return password


class ForcePasswordChangeForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.base.models.password_policy import PasswordPolicy

        self.fields["new_password1"].label = get_translated_message(
            "new_password1_label", _("New password")
        )
        policy = PasswordPolicy.get_active_policy()
        self.fields["new_password1"].help_text = build_password_policy_help_text(policy)
        self.fields["new_password2"].label = get_translated_message(
            "new_password2_label", _("Confirm new password")
        )
        self.fields["new_password2"].help_text = get_translated_message(
            "new_password2_help", _("Repeat your new password.")
        )

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        errors = validate_password_with_policy(password, self.user)
        if errors:
            raise forms.ValidationError(errors)
        return password
