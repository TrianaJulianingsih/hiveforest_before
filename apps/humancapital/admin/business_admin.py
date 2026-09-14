from django.contrib import admin
from apps.humancapital.models.business_models import Business
from apps.base.admin_base import BaseModelAdmin
from apps.base.admin_utils import MassActionMixin

@admin.register(Business)
class BusinessAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "effective", "terminated",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    ordering = ("code",)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name', 'initial', 'shortname', 'description', 'effective', 'terminated', 'remark')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug', 'cat', 'cby', 'uat', 'uby', 'dat', 'dby', 'deleted'),
            'description': 'System related information.',
        }),
    )
