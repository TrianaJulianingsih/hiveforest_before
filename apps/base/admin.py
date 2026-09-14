from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.forms import UserCreationForm as DefaultUserCreationForm
from django.contrib.contenttypes.models import ContentType
from import_export.admin import ImportExportModelAdmin
from apps.base.admin_utils import MassActionMixin
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.models.password_history import PasswordHistory
from apps.base.models.resources import (
    IslandImportRsc,
    ProvinceImportRsc,
    RegencyImportRsc,
    DistrictImportRsc,
    VillageImportRsc,
)
from apps.base.models.locations import (
    Island,
    Province,
    RegencyType,
    Regency,
    District,
    Village,
)
from apps.base.models.sites import Sites
from apps.base.models.entities import CompanyOwner, CompanyOwnership, Company
from apps.base.models.people import Gender, Salutation, Person
from apps.base.models.contacts import (
    Contact,
    ContactContext,
    ContactMedia,
    EmailContact,
    PhoneContact,
    SocialContact,
    SocialPlatform,
    RoleCategory,
    ContactRole,
)
from apps.base.models.reports import PeriodTemplate
from apps.base.models.items import UoM
from apps.base.models.userprofiles import UserProfile
from apps.base.models.credential_ftp import CredentialFTP
from apps.base.models.permissions import Role, CMSPermission, SCMPermission
from apps.base.models.translation import TranslationModule, TranslationKey, Translation
from apps.base.models.password_policy import PasswordPolicy, get_translated_message

from apps.base.models.warehouse import (
    WarehousePalette,
    # CalculationFormula,
    # CalculationVariable,
)
from apps.base.forms.permissionforms import CMSPermissionForm, SCMPermissionForm
from apps.base.forms.profileforms import PersonForm
from import_export.formats.base_formats import CSV, XLSX
from django.utils.translation import gettext_lazy as _
from .user_models import ForcePasswordStatus
from apps.base.models.system_log import SystemLog

from apps.base.models.version import AppVersion, VersionFeature
from django_summernote.admin import SummernoteModelAdmin

from django import forms
import pandas as pd
from django.shortcuts import redirect, render
from django.urls import reverse

from django.utils.safestring import mark_safe

from django.core.exceptions import ValidationError

admin.site.site_title = _("HiveForest")
admin.site.site_header = _("HiveForest")
admin.site.index_title = _("Site Admin")


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


# ═══════════════════════════════════════════════════════════
# FaisalS | Forgot Password function, Periodic Password Change function, Forced Password Change function
# ═══════════════════════════════════════════════════════════
class CustomUserCreationForm(DefaultUserCreationForm):
    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        errors = PasswordPolicy.validate_password(password)
        if errors:
            raise forms.ValidationError(errors)
        return password

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = get_translated_message(
            "new_password1_label", _("Password")
        )
        policy = PasswordPolicy.get_active_policy()
        requirements = []
        if policy:
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
                    get_translated_message(
                        "require_number_error", _("Number required.")
                    )
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
        self.fields["password1"].help_text = ""
        self.fields["password2"].label = get_translated_message(
            "new_password2_label", _("Password confirmation")
        )
        self.fields["password2"].help_text = get_translated_message(
            "new_password2_help", _("Repeat the password.")
        )


class ForcePasswordStatusInline(admin.StackedInline):
    model = ForcePasswordStatus
    can_delete = False
    verbose_name = "Force Password Status"
    verbose_name_plural = "Force Password Status"
    fields = ["must_change_password", "last_reset_at"]
    readonly_fields = ["last_reset_at"]
    extra = 0
    max_num = 1


class CustomUserAdmin(DefaultUserAdmin):
    inlines = [ForcePasswordStatusInline]
    list_display = DefaultUserAdmin.list_display[:-1] + (
        "last_login",
        "is_staff",
        "must_change_password",
    )

    def must_change_password(self, obj):
        try:
            return obj.forcepasswordstatus.must_change_password
        except Exception:
            return False

    must_change_password.boolean = True
    must_change_password.short_description = "Must Change Password"

    def get_inline_instances(self, request, obj=None):
        if obj:
            from .user_models import ForcePasswordStatus

            ForcePasswordStatus.objects.get_or_create(user=obj)
        return super().get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            from .user_models import ForcePasswordStatus

            status, created = ForcePasswordStatus.objects.get_or_create(user=obj)
            if created or not status.must_change_password:
                status.must_change_password = True
                status.save()

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    add_form = CustomUserCreationForm

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = self.add_form
        return super().get_form(request, obj, **kwargs)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
# ═══════════════════════════════════════════════════════════
# // FaisalS | Forgot Password function, Periodic Password Change function, Forced Password Change function
# ═══════════════════════════════════════════════════════════


# Base | Permissions
@admin.register(SCMPermission)
class SCMPermissionAdmin(admin.ModelAdmin):
    form = SCMPermissionForm
    list_display = BaseModelAdmin.list_display_name + (
        "role",
        "distributor_state",
        "branch_state",
        "distitemgroup_state",
        "mfgitemgroup_state",
        "status",
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
        "distributor_state",
        "branch_state",
        "distitemgroup_state",
        "mfgitemgroup_state",
    )

    fields = None
    fieldsets = (
        (
            "Basic Information",
            {  # Fieldset title
                "fields": (
                    "code",
                    "name",
                    "role",
                    "description",
                    "initial",
                    "shortname",
                    "remark",
                    "status",
                    "slug",
                )  # Fields to include in this fieldset
            },
        ),
        (
            "Distributors Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("distributor_state", "distributor"),
                "description": "Grant access to distributor.",  # Optional description
            },
        ),
        (
            "Branches Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("branch_state", "branch"),
                "description": "Grant access to branches.",  # Optional description
            },
        ),
        (
            "Distributor Item Groups Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("distitemgroup_state", "distitemgroup"),
                "description": "Grant access to ditributor item groups.",  # Optional description
            },
        ),
        (
            "Manufacturing Item Groups Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("mfgitemgroup_state", "mfgitemgroup"),
                "description": "Grant access to manufacturing item groups.",  # Optional description
            },
        ),
    )


@admin.register(CMSPermission)
class CMSPermissionAdmin(admin.ModelAdmin):
    form = CMSPermissionForm
    list_display = (
        ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "role",
            "apps_state",
            "mods_state",
            "menu_state",
            "status",
        )
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
        "apps_state",
        "mods_state",
        "menu_state",
    )
    ordering = ("code",)

    fields = None
    fieldsets = (
        (
            "Basic Information",
            {  # Fieldset title
                "fields": (
                    "code",
                    "name",
                    "role",
                    "description",
                    "initial",
                    "shortname",
                    "remark",
                    "status",
                    "slug",
                )  # Fields to include in this fieldset
            },
        ),
        (
            "Application Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("apps_state", "application"),
                "description": "Grant access to applications.",  # Optional description
            },
        ),
        (
            "Module Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("mods_state", "module"),
                "description": "Grant access to modules.",  # Optional description
            },
        ),
        (
            "Menu Permission",
            {
                "classes": ("collapsed",),  # Adds collapsible functionality
                "fields": ("menu_state", "menu"),
                "description": "Grant access to menus.",  # Optional description
            },
        ),
    )


# Base | Users
# __________________________


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
        )
        + BaseModelAdmin.list_display_info
        + ("deleted",)
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )
    fields = (
        "code",
        "name",
        "initial",
        "shortname",
        "group",
        "user",
    )
    autocomplete_fields = (
        "group",
        "user",
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: UserProfileAdmin                                    ║
# ║  Type: ModelAdmin                                          ║
# ║  Purpose: Register UserProfile in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\admin.py                                  ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/14-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("user",)
        + BaseModelAdmin.list_display_name
        + (
            "person__name",
            "person__gender",
        )
        + BaseModelAdmin.list_display_info
        + (
            "language",
            "timezone",
        )
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("user",)
    search_fields = BaseModelAdmin.search_fields + (
        "name",
        "person__first_name",
        "person__last_name",
        "person__nickname",
    )
    fields = (
        "user",
        "person",
        "name",
        "description",
        "remark",
        "language",
        "timezone",
    )
    autocomplete_fields = ("user", "person")

    def get_queryset(self, request):

        # Prefetch related users for optimization
        return super().get_queryset(request).select_related("user")

    def save(self, *args, **kwargs):
        if self.person:
            self.name = self.person.name  # Use the actual stored 'name' field
        super().save(*args, **kwargs)


# Content Types
# __________________________


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ("app_label", "model")
    search_fields = ("app_label", "model")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "codename")
    search_fields = ("name", "codename")


# Base | Items
# __________________________


@admin.register(UoM)
class UoMAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )
    fields = BaseModelAdmin.fields + (
        "code",
        "initial",
        "shortname",
    )


# Base | Reports
# __________________________


@admin.register(PeriodTemplate)
class PeriodeTemplateAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + (
            "version",
            "period",
        )
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "start_month",
            "start_day",
            "end_month",
            "end_day",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "version",
        "period",
        "initial",
        "shortname",
        "start_month",
        "start_day",
        "end_month",
        "end_day",
    )
    fields = BaseModelAdmin.fields + (
        "version",
        "period",
        "initial",
        "shortname",
        "start_month",
        "start_day",
        "end_month",
        "end_day",
    )


# Base | Warehouse
# __________________________


# class CalculationVariableInline(admin.TabularInline):
#     model = CalculationVariable
#     extra = 0
#     fields = (
#         "symbol",
#         "label",
#         "data_type",
#         "default_value",
#         "unit",
#         "source_reference",
#         "status",
#     )
#     show_change_link = True


@admin.register(WarehousePalette)
class WarehousePaletteAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "company",
            "ambient_capacity",
            "ac_room_capacity",
            "capacity",
            "utilized",
            "remaining",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "warehouse_code",
        "company__name",
    )
    list_filter = BaseModelAdmin.list_filter + ("company",)
    readonly_fields = BaseModelAdmin.readonly_fields + ("remaining",)
    autocomplete_fields = ("company",)
    fields = BaseModelAdmin.fields + (
        "code",
        "initial",
        "shortname",
        "company",
        "warehouse_code",
        "ambient_capacity",
        "ac_room_capacity",
        "capacity",
        "utilized",
        "remaining",
    )


# @admin.register(CalculationFormula)
# class CalculationFormulaAdmin(MassActionMixin, BaseModelAdmin):
#     inlines = (CalculationVariableInline,)
#     list_display = (
#         BaseModelAdmin.list_display_id
#         + ("code",)
#         + BaseModelAdmin.list_display_name
#         + ("category", "version", "expression_preview", "targets_display")
#         + BaseModelAdmin.list_display_info
#         + BaseModelAdmin.list_display_last
#     )
#     list_display_links = ("name",)
#     search_fields = BaseModelAdmin.search_fields + (
#         "code",
#         "category",
#         "version",
#         "expression",
#     )
#     list_filter = BaseModelAdmin.list_filter + ("category",)
#     fields = BaseModelAdmin.fields + (
#         "code",
#         "category",
#         "version",
#         "expression",
#         "target_systems",
#         "metadata",
#     )

#     def expression_preview(self, obj):
#         value = (obj.expression or "").strip()
#         return value[:75] + ("…" if len(value) > 75 else "")

#     expression_preview.short_description = "Expression"

#     def targets_display(self, obj):
#         if not obj.target_systems:
#             return "-"
#         return ", ".join(obj.target_systems)

#     targets_display.short_description = "Targets"


# @admin.register(CalculationVariable)
# class CalculationVariableAdmin(MassActionMixin, BaseModelAdmin):
#     list_display = (
#         BaseModelAdmin.list_display_id
#         + ("symbol",)
#         + BaseModelAdmin.list_display_name
#         + ("formula", "data_type", "default_value", "unit")
#         + BaseModelAdmin.list_display_info
#         + BaseModelAdmin.list_display_last
#     )
#     list_display_links = ("name",)
#     search_fields = BaseModelAdmin.search_fields + (
#         "symbol",
#         "label",
#         "formula__code",
#         "formula__name",
#     )
#     list_filter = BaseModelAdmin.list_filter + ("data_type", "formula",)
#     autocomplete_fields = ("formula",)
#     fields = BaseModelAdmin.fields + (
#         "formula",
#         "symbol",
#         "label",
#         "data_type",
#         "default_value",
#         "unit",
#         "source_reference",
#     )


# Base | Contact
# __________________________
@admin.register(ContactMedia)
class ContactMediaAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("group",)
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "name",
        "group",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "group",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(ContactContext)
class ContactContextAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "name",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(SocialPlatform)
class SocialPlatformAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "name",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(Contact)
class ContactAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "person",
            "context",
            "media",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "person",
        "media__name",
        "context__name",
    )
    fields = None
    fieldsets = (
        ("Primary Info", {"fields": ("person", "context", "media", "name")}),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(EmailContact)
class EmailContactAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "person",
            "context",
            "media",
            "email",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "email",
        "person__name",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "person",
                    "context",
                    "media",
                    "email",
                    "name",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(PhoneContact)
class PhoneContactAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "person",
            "context",
            "media",
            "country_code",
            "number",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "country_code",
        "number",
        "person__name",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "person",
                    "context",
                    "media",
                    "country_code",
                    "number",
                    "name",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(SocialContact)
class SocialContactAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "person",
            "context",
            "media",
            "platform",
            "handle",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "platform",
        "handle",
        "person__name",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {"fields": ("person", "context", "media", "platform", "handle", "name")},
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(RoleCategory)
class RoleCategoryAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + (
            "code",
            "initial",
        )
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("name",)
    fields = None
    fieldsets = (
        ("Primary Info", {"fields": ("code", "initial", "name")}),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(ContactRole)
class ContactRoleAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + (
            "code",
            "initial",
        )
        + BaseModelAdmin.list_display_name
        + ("category",)
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("name", "category__name")
    fields = None
    fieldsets = (
        ("Primary Info", {"fields": ("code", "initial", "name", "category")}),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


# Base | People
# __________________________


@admin.register(Person)
class PersonAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("salutation",)
        + BaseModelAdmin.list_display_name
        + (
            "nickname",
            "gender",
            "initial",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "dob",
            "national_id",
            "tax_id",
            "get_roles",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("name", "roles__name")
    autocomplete_fields = ("roles",)
    filter_horizontal = ("roles",)
    form = PersonForm

    def full_name(self, obj):
        return obj.full_name

    full_name.short_description = "Full Name"

    def get_roles(self, obj):
        return ", ".join([role.initial for role in obj.roles.all()])

    get_roles.short_description = "Roles"  # Column title in admin

    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "salutation",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "name",
                    "initial",
                    "nickname",
                    "gender",
                    "roles",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "References",
            {
                "fields": (
                    "national_id",
                    "tax_id",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(Salutation)
class SalutationAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial",)
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code",)
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {"fields": ("code", "name", "initial", "description", "remark")},
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": (
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
                "description": "System related information.",
            },
        ),
    )


@admin.register(Gender)
class GenderAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )


# Base | Entities
# __________________________


@admin.register(CompanyOwner)
class CompanyOwnerAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "owntype")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "owntype__name",
    )
    fields = BaseModelAdmin.fields + (
        "code",
        "initial",
        "shortname",
        "owntype",
    )


@admin.register(CompanyOwnership)
class CompanyOwnershipAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )


@admin.register(Company)
class CompanyAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SitesAdmin                                           ║
# ║  Type: ModelAdmin                                           ║
# ║  Purpose: Register Sites in Admin Site                      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\admin.py                                  ║
# ║  Created: Jun/15-2026 by Copilot                           ║
# ║  Updates: Jun/15-2026 by Copilot                           ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(Sites)
class SitesAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "name",
    )
    fields = BaseModelAdmin.fields + ("code",)


@admin.register(Village)
class VillageAdmin(
    PandasImportMixin, MassActionMixin, BaseModelAdmin, ImportExportModelAdmin
):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("district", "postcode", "longitude", "latitude")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "district__name",
        "postcode",
    )
    resource_class = VillageImportRsc
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {
        "postcode": "string",
        "district": "string",
        "longitude": "string",
        "latitude": "string",
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, request, data):
        """
        Process the imported data and save it to the database.
        """
        for _, row in data.iterrows():
            district_code = row["district"]
            district = District.objects.get(code=district_code)

            latitude = (
                row["latitude"]
                if "latitude" in row and pd.notna(row["latitude"])
                else None
            )
            longitude = (
                row["longitude"]
                if "longitude" in row and pd.notna(row["longitude"])
                else None
            )

            Village.objects.create(
                code=row["code"],
                name=row["name"],
                district=district,
                latitude=latitude,
                longitude=longitude,
                postcode=row["postcode"],
                status=row["status"],
            )

    def get_search_results(self, request, queryset, search_term):
        """
        Override default search behavior:
        - If the request is from the autocomplete field (e.g., in Customer form), search **only by name**.
        - Otherwise, use `search_fields` for the normal list search.
        """
        if (
            "autocomplete" in request.path
        ):  # Detect if request is from an autocomplete field
            queryset = queryset.filter(name__icontains=search_term)

        return super().get_search_results(request, queryset, search_term)


@admin.register(District)
class DistrictAdmin(MassActionMixin, BaseModelAdmin, ImportExportModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("regency", "longitude", "latitude")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "regency__name",
    )
    resource_class = DistrictImportRsc
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]
    list_per_page = 1000

    def get_search_results(self, request, queryset, search_term):
        """
        Override default search behavior:
        - If the request is from the autocomplete field (e.g., in Customer form), search **only by name**.
        - Otherwise, use `search_fields` for the normal list search.
        """
        if (
            "autocomplete" in request.path
        ):  # Detect if request is from an autocomplete field
            queryset = queryset.filter(name__icontains=search_term)

        return super().get_search_results(request, queryset, search_term)


@admin.register(Regency)
class RegencyAdmin(MassActionMixin, BaseModelAdmin, ImportExportModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("type", "province", "capital")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "type__name",
        "province__name",
        "capital",
    )
    resource_class = RegencyImportRsc
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]
    list_per_page = 600

    def get_search_results(self, request, queryset, search_term):
        """
        Override default search behavior:
        - If the request is from the autocomplete field (e.g., in Customer form), search **only by name**.
        - Otherwise, use `search_fields` for the normal list search.
        """
        if (
            "autocomplete" in request.path
        ):  # Detect if request is from an autocomplete field
            queryset = queryset.filter(name__icontains=search_term)

        return super().get_search_results(request, queryset, search_term)


@admin.register(RegencyType)
class RegencyTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code",)


@admin.register(Province)
class ProvinceAdmin(MassActionMixin, BaseModelAdmin, ImportExportModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "shortname",
            "initial",
            "capital",
            "iso",
            "longitude",
            "latitude",
            "island",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "shortname",
        "initial",
        "capital",
        "iso",
        "island__name",
    )
    resource_class = ProvinceImportRsc
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]

    def get_search_results(self, request, queryset, search_term):
        """
        Override default search behavior:
        - If the request is from the autocomplete field (e.g., in Customer form), search **only by name**.
        - Otherwise, use `search_fields` for the normal list search.
        """
        if (
            "autocomplete" in request.path
        ):  # Detect if request is from an autocomplete field
            queryset = queryset.filter(name__icontains=search_term)

        return super().get_search_results(request, queryset, search_term)


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: IslandAdmin                                           ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering Island in Admin Site                   ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: by Setiadji                                        ║
# ║  Updates: Jul/18 by Setiadji                                 ║
# ╚══════════════════════════════════════════════════════════════╝
@admin.register(Island)
class IslandAdmin(MassActionMixin, BaseModelAdmin, ImportExportModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "iso",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    ordering = ("code",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "iso",
    )
    resource_class = IslandImportRsc
    import_formats = [CSV, XLSX]
    export_formats = [CSV, XLSX]
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "iso",
                    "description",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "remark", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ═══════════════════════════════════════════════════════════
# FaisalS | Forgot Password function, Periodic Password Change function, Forced Password Change function
# ═══════════════════════════════════════════════════════════
from django import forms
from django.contrib.auth.models import User
from .user_models import ForcePasswordStatus


class ForcePasswordStatusForm(forms.ModelForm):
    class Meta:
        model = ForcePasswordStatus
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "user" in self.fields:
            used_user_ids = ForcePasswordStatus.objects.values_list("user_id", flat=True)
            if self.instance and self.instance.pk:
                allowed_ids = list(
                    User.objects.exclude(id__in=used_user_ids).values_list("id", flat=True)
                )
                if self.instance.user_id:
                    allowed_ids.append(self.instance.user_id)
                self.fields["user"].queryset = User.objects.filter(id__in=allowed_ids)
            else:
                self.fields["user"].queryset = User.objects.exclude(id__in=used_user_ids)


@admin.register(ForcePasswordStatus)
class ForcePasswordStatusAdmin(admin.ModelAdmin):
    form = ForcePasswordStatusForm
    list_display = ["user", "must_change_password", "last_reset_at"]
    list_filter = ["must_change_password", "last_reset_at"]
    search_fields = ["user__username", "user__email"]
    ordering = ["user__username"]
    raw_id_fields = ["user"]
    autocomplete_fields = ["user"]
    readonly_fields = ["last_reset_at"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["user", "last_reset_at"]
        return ["last_reset_at"]
    
    fieldsets = (
        (
            "User Information",
            {
                "fields": ("user",),
            },
        ),
        (
            "Password Status",
            {
                "fields": ("must_change_password", "last_reset_at"),
            },
        ),
    )


# ═══════════════════════════════════════════════════════════
# FaisalS | Translation Admin - Custom Translation System
# ═══════════════════════════════════════════════════════════
class TranslationInline(admin.StackedInline):
    model = Translation
    extra = 0
    fields = ["language", "value", "status"]
    verbose_name = "Translation"
    verbose_name_plural = "Translations by Language"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Customize form fields for better display"""
        if db_field.name == "value":
            kwargs["widget"] = admin.widgets.AdminTextareaWidget(
                attrs={
                    "rows": 3,
                    "cols": 80,
                    "style": "width: 100%; font-family: monospace;",
                }
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(TranslationModule)
class TranslationModuleAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "description", "status", "cat", "cby"]
    list_filter = ["status"]
    search_fields = ["code", "name", "description"]
    ordering = ["code"]

    fieldsets = (
        ("Module Information", {"fields": ("code", "name", "description", "status")}),
        (
            "Metadata",
            {"fields": ("cat", "cby", "uat", "uby"), "classes": ("collapse",)},
        ),
    )


@admin.register(TranslationKey)
class TranslationKeyAdmin(admin.ModelAdmin):
    list_display = ["module", "key", "name", "default_value_preview", "status"]
    list_filter = ["module", "status"]
    search_fields = ["key", "name", "default_value"]
    ordering = ["module", "key"]
    inlines = [TranslationInline]

    fieldsets = (
        ("Key Information", {"fields": ("module", "key", "name")}),
        (
            "Default Value",
            {
                "fields": ("default_value",),
                "description": "This is the fallback value when no translation is available.",
            },
        ),
        ("Settings", {"fields": ("status", "description"), "classes": ("collapse",)}),
    )

    def default_value_preview(self, obj):
        """Show preview of default value"""
        if not obj.default_value:
            return "-"
        return (
            obj.default_value[:50] + "..."
            if len(obj.default_value) > 50
            else obj.default_value
        )

    default_value_preview.short_description = "Default Value"


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ["translation_key", "language", "value_preview", "status"]
    list_filter = ["language", "translation_key__module", "status"]
    search_fields = ["translation_key__key", "value"]
    ordering = ["translation_key", "language"]

    def value_preview(self, obj):
        return obj.value[:100] + "..." if len(obj.value) > 100 else obj.value

    value_preview.short_description = "Value"


# ═══════════════════════════════════════════════════════════
# // FaisalS | Translation Admin - Custom Translation System
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# FaisalS | Version History App
# ═══════════════════════════════════════════════════════════


class VersionFeatureInline(admin.TabularInline):
    model = VersionFeature
    extra = 1
    fields = ["feature_type", "title", "description", "order"]
    ordering = ["order"]


@admin.register(AppVersion)
class AppVersionAdmin(SummernoteModelAdmin):
    summernote_fields = ("description",)
    list_display = [
        "version_number",
        "title",
        "release_date",
        "is_current",
        "is_major_release",
        "feature_count",
        "cat",
        "cby",
        "uat",
        "uby",
        "dat",
        "dby",
        "deleted",
    ]
    list_filter = ["is_current", "is_major_release", "release_date"]
    search_fields = ["version_number", "title", "description"]
    ordering = ["-release_date", "-version_number"]
    date_hierarchy = "release_date"

    fieldsets = (
        (
            _("Version Information"),
            {"fields": ("version_number", "title", "release_date")},
        ),
        (_("Status"), {"fields": ("is_current", "is_major_release")}),
        (_("Description"), {"fields": ("description",)}),
    )

    inlines = [VersionFeatureInline]

    def feature_count(self, obj):
        return obj.features.count()

    feature_count.short_description = _("Features")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_current:
            AppVersion.objects.exclude(pk=obj.pk).update(is_current=False)


@admin.register(VersionFeature)
class VersionFeatureAdmin(SummernoteModelAdmin):
    summernote_fields = ("description",)
    list_display = [
        "version",
        "feature_type",
        "title",
        "order",
        "cat",
        "cby",
        "uat",
        "uby",
        "dat",
        "dby",
        "deleted",
    ]
    list_filter = ["feature_type", "version"]
    search_fields = ["title", "description"]
    ordering = ["version", "order"]

    fieldsets = (
        (
            _("Feature Information"),
            {"fields": ("version", "feature_type", "title", "order")},
        ),
        (_("Description"), {"fields": ("description",)}),
    )


# ═══════════════════════════════════════════════════════════
# // FaisalS | Version History App
# ═══════════════════════════════════════════════════════════



# FaisalS | HF-75 - Master Password Policy
class PasswordPolicyForm(forms.ModelForm):
    class Meta:
        model = PasswordPolicy
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        min_length = cleaned_data.get("min_length")
        max_length = cleaned_data.get("max_length")

        if min_length and max_length and min_length > max_length:
            raise ValidationError(
                "Minimum length cannot be greater than maximum length."
            )

        return cleaned_data


@admin.register(PasswordPolicy)
class PasswordPolicyAdmin(admin.ModelAdmin):
    form = PasswordPolicyForm

    list_display = [
        "min_length",
        "max_length",
        "require_lowercase",
        "require_uppercase",
        "require_number",
        "require_special",
        "require_space",
        "password_history_limit",
        "check_password_history",
        "password_expiry_days",
        "updated_at",
    ]

    list_filter = [
        "require_lowercase",
        "require_uppercase",
        "require_number",
        "require_special",
        "require_space",
        "check_password_history",
    ]

    ordering = ["-updated_at"]

    readonly_fields = ["updated_at"]

    fieldsets = (
        (
            "Password Length Settings",
            {
                "fields": ("min_length", "max_length"),
            },
        ),
        (
            "Character Requirements",
            {
                "fields": (
                    "require_lowercase",
                    "require_uppercase",
                    "require_number",
                    "require_special",
                    "require_space",
                ),
            },
        ),
        (
            "Password History Settings",
            {
                "fields": (
                    "password_history_limit",
                    "check_password_history",
                ),
                "description": "Configure password history validation. Set password_history_limit to 0 to disable history tracking.",
            },
        ),
        (
            "Password Expiry Settings",
            {
                "fields": (
                    "password_expiry_days",
                    "password_expiry_warning_days",
                ),
                "description": "Configure password expiration. Set password_expiry_days to 0 to disable expiration.",
            },
        ),
        (
            "System Information",
            {
                "fields": ("updated_at",),
            },
        ),
    )

    def has_add_permission(self, request):
        # Hanya boleh ada 1 policy
        if PasswordPolicy.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # Tidak boleh dihapus
        return False


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "created_at_display",
        "changed_by_display",
        "policy_status",
    ]

    list_filter = [
        "created_at",
        "changed_by",
        "user",
    ]

    search_fields = [
        "user__username",
        "user__email",
    ]

    ordering = ["-created_at"]

    readonly_fields = [
        "user",
        "password_hash",
        "created_at",
        "changed_by",
        "history_info_display",
    ]

    fieldsets = (
        (
            "Password History Information",
            {
                "fields": (
                    "history_info_display",
                    "user",
                    "created_at",
                    "changed_by",
                ),
            },
        ),
        (
            "Password Hash (Hashed for Security)",
            {
                "classes": ("collapse",),
                "fields": ("password_hash",),
                "description": "The password is stored as a secure hash (one-way encryption). It cannot be reversed to get the original password.",
            },
        ),
    )

    def created_at_display(self, obj):
        """Display formatted created_at timestamp"""
        from django.utils import timezone
        from django.utils.html import format_html

        local_time = timezone.localtime(obj.created_at)
        days_ago = (timezone.now() - obj.created_at).days

        if days_ago == 0:
            time_str = "Today"
        elif days_ago == 1:
            time_str = "Yesterday"
        else:
            time_str = f"{days_ago} days ago"

        return format_html(
            '<span title="{}">{}</span>',
            local_time.strftime("%Y-%m-%d %H:%M:%S"),
            time_str,
        )

    created_at_display.short_description = "Changed At"

    def changed_by_display(self, obj):
        """Display changed_by with color coding"""
        from django.utils.html import format_html

        colors = {
            "user": "#3498db",  # Blue
            "forgot_password": "#e74c3c",  # Red
            "force_change": "#f39c12",  # Orange
            "admin": "#9b59b6",  # Purple
        }

        color = colors.get(obj.changed_by, "#95a5a6")  # Gray default

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.changed_by.replace("_", " ").title(),
        )

    changed_by_display.short_description = "Changed By"

    def policy_status(self, obj):
        from django.utils.html import format_html

        policy = PasswordPolicy.get_active_policy()

        if (
            not policy
            or policy.password_history_limit == 0
            or not policy.check_password_history
        ):
            return format_html(
                '<span style="color: #95a5a6;">{}</span>', "Policy Inactive"
            )

        user_history_count = (
            PasswordHistory.objects.filter(user=obj.user)
            .order_by("-created_at")
            .count()
        )

        if user_history_count <= policy.password_history_limit:
            return format_html(
                '<span style="color:#27ae60;font-weight:bold;">{}</span>', "✓ Active"
            )
        else:
            return format_html('<span style="color:#e74c3c;">{}</span>', "✗ Expired")

    policy_status.short_description = "Policy Status"

    def history_info_display(self, obj):

        policy = PasswordPolicy.get_active_policy()
        user_history = PasswordHistory.objects.filter(user=obj.user).order_by(
            "-created_at"
        )

        info_html = f"""
        <div style="background-color: #ecf0f1; padding: 10px; border-radius: 5px;">
            <p><strong>User:</strong> {obj.user.username} ({obj.user.email})</p>
            <p><strong>Password Changed:</strong> {obj.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Changed By:</strong> {obj.changed_by}</p>
            <hr style="border: none; border-top: 1px solid #bdc3c7; margin: 10px 0;">
            <p><strong>Policy Settings:</strong></p>
            <ul style="list-style-position: inside;">
                <li>History Limit: {policy.password_history_limit if policy else 'N/A'} passwords</li>
                <li>Check History: {policy.check_password_history if policy else 'N/A'}</li>
                <li>Total History Entries: {user_history.count()}</li>
            </ul>
        </div>
        """

        return mark_safe(info_html)

    history_info_display.short_description = "Password History Details"

    def has_add_permission(self, request):
        # Password history should only be created programmatically
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion only for superusers
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Password history is read-only
        return False
# Base | Credentials FTP
# __________________________


@admin.register(CredentialFTP)
class CredentialFTPAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + ("username", "url", "periode")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    # password sengaja TIDAK ditampilkan di list (keamanan)
    search_fields = BaseModelAdmin.search_fields + ("username", "url", "periode")
    fields = BaseModelAdmin.fields + ("username", "password", "url", "periode")


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = [
        "cat",
        "user",
        "action",
        "module",
        "feature",
        "status",
        "response_code",
        "object_type",
        "object_id",
        "ip_address",
    ]
    
    list_filter = [
        "cat",
        "user",
        "action",
        "module",
        "feature",
        "status",
        "log_type",
        "response_code",
        "object_type",
        "object_id",
    ]
    
    search_fields = [
        "user__username",
        "description",
        "object_id",
        "request_path",
        "error_message",
    ]
    
    ordering = ["-cat"]
    
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CustomAdminSite(AdminSite):
    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_staff


admin_site = CustomAdminSite()

from apps.base.admin_authentication import *  # noqa: F401,F403,E402
