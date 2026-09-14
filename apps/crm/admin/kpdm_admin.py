from django.contrib import admin
from apps.base.admin_base import BaseModelAdmin
from apps.base.admin_utils import MassActionMixin
from apps.crm.models.kpdm_models import KPDMContact, KPDMCustomer

# CRM | KMPDM
# __________________________

@admin.register(KPDMContact)
class KPDMContactAdmin(MassActionMixin, BaseModelAdmin):
    list_display = ('name', 'person',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('person', 'name', 'description', 'remark')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug', 'cat', 'cby', 'uat', 'uby', 'dat', 'dby', 'deleted'),
            'description': 'System related information.',
        }),
    )

@admin.register(KPDMCustomer)
class KPDMCustomerAdmin(admin.ModelAdmin):
    list_display = ['kpdm', 'customer', 'assigned_by', 'assigned_at']
    autocomplete_fields = ['kpdm', 'customer']
    search_fields = ['kpdm__person__name', 'customer__name', 'customer__code']
    ordering = ['kpdm__person__name']
    def get_queryset(self, request):
        return super().get_queryset(request)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct

    class Media:
        css = {
            'all': ('static/admin/css/widget.css',)  # load custom css
        }
    
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('kpdm', 'customer')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug',),
            'description': 'System related information.',
        }),
    )
