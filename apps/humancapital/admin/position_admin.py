from django.contrib import admin
from django.urls import reverse
import pandas as pd
from apps.humancapital.models.structure_models import Position, Organization
from apps.humancapital.models.employee_models import EmployeeTitle
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: PositionAdmin                                       ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Position in Admin Site               ║
# ╟────────────────────────────────────────────────────────────⢢
# ║  Path: apps\humancapital\admin\position_admin.py           ║
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
