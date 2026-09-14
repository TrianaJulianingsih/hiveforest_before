from django.contrib import admin
from apps.cms.models.app_managers_models import ApplicationList
from apps.base.admin_base import BaseModelAdmin
from modeltranslation.admin import TranslationAdmin

@admin.register(ApplicationList)
class ApplicationListAdmin(TranslationAdmin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
        )
        + BaseModelAdmin.list_display_info
        + ("icon", "status", "cat", "uat", "order")
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )
    fields = (
        ("code",)
        + BaseModelAdmin.fields_name
        + (
            "initial",
            "shortname",
            "icon",
            "order",
        )
        + BaseModelAdmin.fields_info
        + BaseModelAdmin.fields_last
    )
    ordering = ("name",)
