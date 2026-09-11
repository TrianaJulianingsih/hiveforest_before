from django.contrib import admin
from apps.cms.models.menusystem import MenuItem
from apps.cms.models.appmanagers import ApplicationList
from apps.cms.models.modmanagers import ModuleList
from apps.base.admin_base import BaseModelAdmin
from apps.base.admin_utils import MassActionMixin
from django.db.models import Q, Value
from django.db.models.functions import Concat
from modeltranslation.admin import TranslationAdmin


# Register your models here.
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


@admin.register(ModuleList)
class ModuleListAdmin(BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "application")
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
            "application",
            "order",
        )
        + BaseModelAdmin.fields_info
        + BaseModelAdmin.fields_last
    )
    ordering = ("name",)
    autocomplete_fields = ("application",)

    # Override __str__ to show concatenated text
    def __str__(self):
        return f"{self.name} | {self.application}"  # This controls dropdown display

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        if search_term:
            queryset = queryset.filter(Q(description__icontains=search_term))
        return queryset, use_distinct


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
