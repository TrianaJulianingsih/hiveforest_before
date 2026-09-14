import pandas as pd
from django.contrib import admin
from django.urls import reverse

from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.crm.models.hospital_models import Association

@admin.register(Association)
class AssociationAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ("code",) + BaseModelAdmin.list_display_name + \
        ("initial", "shortname",) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname",)
    list_per_page = 1000
    has_pandas_import = True

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

            # Handle Blank Fields
            code =  handle_blank(row['code'])
            description = handle_blank(row['description'])
            remark =  handle_blank(row['remark'])
            initial =  handle_blank(row['initial'])
            shortname =  handle_blank(row['shortname'])

            Association.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                status=row['status']
            )
