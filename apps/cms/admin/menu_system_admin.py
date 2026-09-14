from django.contrib import admin
from apps.cms.models.menu_system_models import MenuItem
from apps.base.admin_base import BaseModelAdmin

@admin.register(MenuItem)
class MenuItemAdmin(BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
        )
        + BaseModelAdmin.list_display_info
        + (
            "parent",
            "application",
            "module",
            "icon",
            "url",
            "iframe_url",
            "order",
        )
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "url",
        "module__name",
        "module__application",
        "module__description",
    )
    fields = (
        ("code",)
        + BaseModelAdmin.fields_name
        + (
            "initial",
            "shortname",
            "parent",
            "application",
            "module",
            "icon",
            "url",
            "iframe_url",
            "order",
        )
        + BaseModelAdmin.fields_info
        + BaseModelAdmin.fields_last
    )
    autocomplete_fields = (
        "parent",
        "application",
        "module",
    )
