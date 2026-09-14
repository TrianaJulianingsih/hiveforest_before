from django.contrib import admin
from django.urls import reverse
import pandas as pd
from apps.humancapital.models.employee_models import Employee, EmployeeTitle
from apps.base.models.people import Gender
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin

def person_field_display(field_name, label=None):
    def _func(self, obj):
        return getattr(obj.person, field_name, "-") if obj.person else "-"
    _func.short_description = label or field_name.replace("_", " ").title()
    _func.admin_order_field = f"person__{field_name}"
    return _func

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: EmployeeAdmin                                       ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Employee in Admin Site               ║
# ╟────────────────────────────────────────────────────────────⢢
# ║  Path: apps\humancapital\admin\employee_admin.py           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/28-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
@admin.register(Employee)
class EmployeeAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ('code',) + BaseModelAdmin.list_display_name  + ('hired', 'terminated',) + \
        ('person', 'person__initial', 'person__nickname', 'person__gender', 'person__dob', 'person__national_id', 'person__tax_id',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('name',)
    list_per_page = 1000
    has_pandas_import = True
    ordering = ('name',)
    search_fields = BaseModelAdmin.search_fields + ('code', 'person__initial', 'person__nickname', 'person__national_id', 'person__tax_id', 'person__name',)

    person__initial = person_field_display('initial', 'Initial')
    person__nickname = person_field_display('nickname', 'Nickname')
    person__gender = person_field_display('gender', 'Gender')
    person__dob = person_field_display('dob', 'Birth Date')
    person__national_id = person_field_display('national_id', 'NationalID')
    person__tax_id = person_field_display('tax_id', 'TaxID')

    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'person', 'name',  'description', 'remark',)
        }),
        ('References', {
            'fields': ('hired', 'terminated',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug', 'cat', 'cby', 'uat', 'uby', 'dat', 'dby', 'deleted'),
            'description': 'System related information.',
        }),
    )

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context['has_pandas_import'] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        def handle_blank(value):
            """
            Convert blank or NaN values to None for decimal fields.
            """
            if pd.isna(value) or value == '':
                return None
            return value

        for _, row in data.iterrows():
            gender_name = row['gender']
            gender = None  # Default to None if blank
            if pd.notna(gender_name) and gender_name.strip() != '':
                try:
                    gender = Gender.objects.get(code=gender_name)
                except Gender.DoesNotExist:
                    gender = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])
            hired = handle_blank(row['hired'])
            terminated = handle_blank(row['terminated'])
            dob = handle_blank(row['dob'])
            citizenship_id = handle_blank(row['citizenship_id'])
            tax_id = handle_blank(row['tax_id'])

            Employee.objects.create(
                code=code,
                name=row['name'],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                gender=gender,
                dob=dob,
                hired=hired,
                terminated=terminated,
                citizenship_id=citizenship_id,
                tax_id=tax_id,
                status=row['status']
            )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: EmployeeTitleAdmin                                  ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Employee Title in Admin Site         ║
# ╟────────────────────────────────────────────────────────────⢢
# ║  Path: apps\humancapital\admin\employee_admin.py           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(EmployeeTitle)
class EmployeeTitleAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
