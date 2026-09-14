from django.contrib import admin
from apps.cms.models.module_managers_models import ModuleList
from apps.base.admin_base import BaseModelAdmin
from django.db.models import Q

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
