from django.contrib import admin
from apps.humancapital.models.structure_models import Organization, OrganizationType
from apps.base.admin_base import BaseModelAdmin
from apps.base.admin_utils import MassActionMixin

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: OrganizationAdmin                                   ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Organization in Admin Site           ║
# ╟────────────────────────────────────────────────────────────⢢
# ║  Path: apps\humancapital\admin\organization_admin.py       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/6-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(Organization)
class OrganizationAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ('initial', 'shortname', 'type', 'parent', 'effective', 'terminated',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ('code', 'initial', 'shortname', 'type', 'parent')
    ordering = ('code',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name', 'initial', 'shortname', 'type', 'parent', 'description', 'effective', 'terminated', )
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: OrganizationTypeAdmin                               ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering OrganizataionType in Admin Site      ║
# ╟────────────────────────────────────────────────────────────⢢
# ║  Path: apps\humancapital\admin\organization_admin.py       ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝ 
@admin.register(OrganizationType)
class OrganizationTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
          ("initial",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial",)
    
    fields = (
        "code",
        "initial",
        "name",
        "description",
        "remark",
        "status",
        "slug",
    )
