from django.contrib import admin
from apps.humancapital.models.business import Business
from apps.humancapital.models.structure import Assignment, Position, Organization, OrganizationType
from apps.humancapital.models.employee import Employee, EmployeeTitle
from apps.base.models.people import Gender
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin

# Pandas
from django import forms
import pandas as pd
from django.shortcuts import redirect, render
from django.urls import reverse

class CsvImportForm(forms.Form):
     csv_file = forms.FileField()


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

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AssignmentAdmin                                     ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Position in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\admin.py                          ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/2-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(Assignment)
class AssignmentAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname", "effective", "terminated", "position", "employee", "title",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = ("name", "code", "description", "remark", "initial", "shortname", "effective", "terminated", "position", "employee")
    list_per_page = 1000
    has_pandas_import = True
    fields = ("employee", "position", "title",) + BaseModelAdmin.fields + ("code", "initial", "shortname", "effective", "terminated")
    autocomplete_fields = ('employee', 'position')

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
        def clean_code(value):
            """
            Clean and format the 'code' value:
            - Remove trailing '.0' if it's an integer.
            - Convert NaN/empty values to None.
            """
            if pd.isna(value) or value == '':
                return None
            value = str(value).strip()  # Ensure the value is a string and strip whitespace
            if value.endswith('.0'):  # Handle float-like integers
                value = value[:-2]
            return value

        # Clean the 'code' column
        data['code'] = data['code'].apply(clean_code)

        for _, row in data.iterrows():

            position_code = row['position']
            position = None  # Default to None if blank
            if pd.notna(position_code) and position_code.strip() != '':
                try:
                    position = Position.objects.get(code=position_code)
                except Position.DoesNotExist:
                    position = None  # Handle as per your business logic

            employee_code = row['employee']
            employee = None  # Default to None if blank
            if pd.notna(employee_code) and employee_code.strip() != '':
                try:
                    employee = Employee.objects.get(code=employee_code)
                except Employee.DoesNotExist:
                    employee = None  # Handle as per your business logic

            title_code = row['title']
            title = None  # Default to None if blank
            if pd.notna(title_code) and title_code.strip() != '':
                try:
                    title = EmployeeTitle.objects.get(code=title_code)
                except EmployeeTitle.DoesNotExist:
                    title = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])
            effective =  handle_blank(row['effective'])
            terminated =  handle_blank(row['terminated'])

            Assignment.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                effective=effective,
                terminated=terminated,
                position=position,
                employee=employee,
                title=title,
                status=row['status']
            )

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: PositionAdmin                                       ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Position in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\admin.py                          ║
# ║  Created: Jun/18-2025 by Setiadji                          ║
# ║  Updates: Jun/19-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(Position)
class PositionAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ('code',) + BaseModelAdmin.list_display_name + \
        ('initial', 'shortname', 'level', 'title',  'parent', 'organization', 'effective', 'terminated') + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ('name',)
    list_per_page = 1000
    has_pandas_import = True
    search_fields = BaseModelAdmin.search_fields + ('code', 'initial', 'shortname', 'level')
    ordering = ('name',)
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('code', 'name', 'initial', 'shortname', 'level', 'title', 'description', 'parent', 'organization', 'effective', 'terminated', 'remark')
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'slug'),
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
        def clean_code(value):
            """
            Clean and format the 'code' value:
            - Remove trailing '.0' if it's an integer.
            - Convert NaN/empty values to None.
            """
            if pd.isna(value) or value == '':
                return None
            value = str(value).strip()  # Ensure the value is a string and strip whitespace
            if value.endswith('.0'):  # Handle float-like integers
                value = value[:-2]
            return value

        # Clean the 'code' column
        data['code'] = data['code'].apply(clean_code)
        data['parent'] = data['parent'].apply(clean_code)

        for _, row in data.iterrows():
            title_code = row['title']
            title = None  # Default to None if blank
            if pd.notna(title_code) and title_code.strip() != '':
                try:
                    title = EmployeeTitle.objects.get(code=title_code)
                except EmployeeTitle.DoesNotExist:
                    title = None  # Handle as per your business logic

            parent_code = row['parent']
            parent = None  # Default to None if blank
            if pd.notna(parent_code) and parent_code.strip() != '':
                try:
                    parent = Position.objects.get(code=parent_code)
                except Position.DoesNotExist:
                    parent = None  # Handle as per your business logic

            organization_code = row['organization']
            organization = None  # Default to None if blank
            if pd.notna(organization_code) and organization_code.strip() != '':
                try:
                    organization = Organization.objects.get(code=organization_code)
                except Organization.DoesNotExist:
                    organization = None  # Handle as per your business logic

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])
            level =  handle_blank(row['level'])
            effective =  handle_blank(row['effective'])

            if Position.objects.filter(code=code).exists():
                print(f"Record with code {code} already exists. Skipping.")
                continue

            Position.objects.create(
                code=code,
                name=row["name"],
                title=title,
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                level=level,
                effective=effective,
                parent=parent,
                organization=organization,
                status=row['status']
            )

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
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\admin.py                          ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/28-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝ 
@admin.register(Employee)
class EmployeeAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ('code',) + BaseModelAdmin.list_display_name  + ('hired', 'terminated', 'employment_status',) + \
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
            'fields': ('hired', 'terminated', 'employment_status',)
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
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\admin.py                          ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(EmployeeTitle)
class EmployeeTitleAdmin(MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: OrganizationAdmin                                   ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Organization in Admin Site           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\admin.py                          ║
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
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\admin.py                          ║
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
    