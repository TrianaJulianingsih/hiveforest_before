from django.contrib import admin
from django.utils.html import format_html

from apps.base.admin_base import BaseModelAdmin
from apps.base.forms.authentication_forms import (
    AuthenticationSettingAdminForm,
    UserAuthenticationAdminForm,
)
from apps.base.models.authentication_models import (
    AuthenticationLog,
    AuthenticationSetting,
    UserAuthentication,
)
from apps.base.services.entra_service import is_oidc_available
from apps.base.utils.authentication_utils import (
    generate_authenticator_secret,
    get_authenticator_qr_base64,
    get_authenticator_provisioning_uri,
)


@admin.register(AuthenticationSetting)
class AuthenticationSettingAdmin(BaseModelAdmin):
    form = AuthenticationSettingAdminForm
    fields = None
    list_display = (
        "name",
        "enable_local_login",
        "enable_microsoft_login",
        "require_mfa",
        "auto_create_user",
        "auto_update_user",
    )
    readonly_fields = BaseModelAdmin.readonly_fields + ("oidc_status",)
    fieldsets = (
        (
            "General",
            {
                "fields": (
                    "name",
                    "enable_local_login",
                    "enable_microsoft_login",
                    "require_mfa",
                    "auto_create_user",
                    "auto_update_user",
                    "oidc_status",
                )
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "allowed_email_domains",
                )
            },
        ),
        (
            "Default User",
            {
                "fields": (
                    "default_user_is_active",
                    "default_user_is_staff",
                    "default_user_is_superuser",
                )
            },
        ),
        (
            "UI",
            {
                "fields": (
                    "login_button_text",
                    "login_message",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "enable_login_log",
                    "enable_logout_log",
                    "enable_failed_login_log",
                )
            },
        ),
        (
            "System",
            {
                "classes": ("collapsed",),
                "fields": (
                    "description",
                    "remark",
                    "status",
                    "slug",
                    "cat",
                    "cby",
                    "uat",
                    "uby",
                    "dat",
                    "dby",
                    "deleted",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return not AuthenticationSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def oidc_status(self, obj):
        return "Installed" if is_oidc_available() else "Missing dependency: mozilla-django-oidc"

    oidc_status.short_description = "OIDC Package Status"


@admin.register(UserAuthentication)
class UserAuthenticationAdmin(admin.ModelAdmin):
    form = UserAuthenticationAdminForm
    list_display = (
        "user",
        "authentication_enabled",
        "allow_local_login",
        "allow_microsoft_login",
        "require_mfa",
        "authenticator_confirmed",
        "updated_at",
    )
    search_fields = ("user__username", "user__email")
    list_filter = (
        "authentication_enabled",
        "allow_local_login",
        "allow_microsoft_login",
        "require_mfa",
        "authenticator_confirmed",
    )
    autocomplete_fields = ("user",)
    readonly_fields = (
        "authenticator_provisioning_uri",
        "authenticator_qr_preview",
        "authenticator_last_verified_at",
    )
    fieldsets = (
        (
            "User Access",
            {
                "fields": (
                    "user",
                    "authentication_enabled",
                    "allow_local_login",
                    "allow_microsoft_login",
                    "require_mfa",
                )
            },
        ),
        (
            "Authenticator Setup",
            {
                "fields": (
                    "authenticator_secret",
                    "authenticator_confirmed",
                    "authenticator_last_verified_at",
                    "authenticator_provisioning_uri",
                    "authenticator_qr_preview",
                ),
                "description": "If MFA is enabled and no secret exists, a new secret will be generated automatically on save.",
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if obj.require_mfa and not obj.authenticator_secret:
            obj.authenticator_secret = generate_authenticator_secret()
        if not obj.require_mfa:
            obj.authenticator_confirmed = False
        super().save_model(request, obj, form, change)

    def authenticator_provisioning_uri(self, obj):
        if not obj.authenticator_secret:
            return "Save with MFA enabled to generate authenticator secret."
        return get_authenticator_provisioning_uri(obj.user, obj.authenticator_secret)

    authenticator_provisioning_uri.short_description = "Authenticator URI"

    def authenticator_qr_preview(self, obj):
        if not obj.authenticator_secret:
            return "QR preview is available after the secret is generated."
        encoded = get_authenticator_qr_base64(obj.user, obj.authenticator_secret)
        if not encoded:
            return "Install package 'qrcode' to render QR preview in admin."
        return format_html(
            '<img src="data:image/png;base64,{}" alt="Authenticator QR" style="max-width:220px;" />',
            encoded,
        )

    authenticator_qr_preview.short_description = "Scan With Authenticator"


@admin.register(AuthenticationLog)
class AuthenticationLogAdmin(admin.ModelAdmin):
    list_display = (
        "login_time",
        "user",
        "username",
        "login_method",
        "login_result",
        "ip_address",
        "browser",
        "operating_system",
        "logout_time",
    )
    list_filter = ("login_method", "login_result", "browser", "operating_system")
    search_fields = ("user__username", "user__email", "username", "ip_address", "failure_reason")
    readonly_fields = [field.name for field in AuthenticationLog._meta.fields]
    date_hierarchy = "login_time"
    ordering = ("-login_time",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
