from django import forms
from django.contrib import admin
from django.urls import reverse
import pandas as pd
from apps.humancapital.models.structure_models import Assignment, Position
from apps.humancapital.models.employee_models import Employee, EmployeeTitle
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AssignmentAdmin                                     ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Position in Admin Site               ║
# ╟────────────────────────────────────────────────────────────⢢
# ║  Path: apps\humancapital\admin\assignment_admin.py         ║
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
