from django import forms

from apps.base.models.authentication_models import AuthenticationSetting, UserAuthentication


class AuthenticationSettingAdminForm(forms.ModelForm):
    class Meta:
        model = AuthenticationSetting
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["allowed_email_domains"].widget.attrs.update(
            {
                "rows": 4,
                "placeholder": "company.com\nsubsidiary.company.com",
            }
        )
        self.fields["login_button_text"].widget.attrs.update(
            {"placeholder": "Sign in with Microsoft"}
        )
        self.fields["login_message"].widget.attrs.update(
            {"placeholder": "Sign in to start your session"}
        )


class MFAVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="Authenticator Code",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "placeholder": "Enter 6-digit code",
            }
        ),
    )

    def clean_otp_code(self):
        otp_code = (self.cleaned_data.get("otp_code") or "").strip().replace(" ", "")
        if not otp_code.isdigit():
            raise forms.ValidationError("Authenticator code must be numeric.")
        return otp_code


class UserAuthenticationAdminForm(forms.ModelForm):
    class Meta:
        model = UserAuthentication
        fields = "__all__"
