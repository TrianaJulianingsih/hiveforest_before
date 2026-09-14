import pandas as pd
from django.contrib import admin, messages
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import redirect, render

from apps.base.models.items import UoM
from apps.finance.models.products_models import ItemPrice
from apps.supplychain.models.distributions_models import Distributor, DistributorItem
from apps.sales.models.sales_models import SalesType
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.filters import DeletedListFilter, StatusListFilter, EffectiveYearFilter

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ItemPriceAdmin                                      ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering ItemPrice in Admin Site              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Aug/27-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝  
@admin.register(ItemPrice)
class ItemPriceAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = BaseModelAdmin.list_display_id + ('code', 'distributor', 'distitem',) + BaseModelAdmin.list_display_name + \
        ('salestype', 'hna', 'hjp', 'pct_pm', 'pct_advdisc', 'priceuom', 'conversionsize', 'effective',) + BaseModelAdmin.list_display_info + BaseModelAdmin.list_display_last
    list_display_links = ("code",)
    search_fields = BaseModelAdmin.search_fields + ('id', 'code', 'salestype__name', 'hna', 'hjp', 'pct_pm', 'pct_advdisc', 'effective', 'priceuom__name', 'conversionsize')
    list_per_page = 1000
    has_pandas_import = True
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
        'distributor',
        'salestype',
        EffectiveYearFilter
    )
    fields = None
    fieldsets = (
        ('Primary Info', {
            'fields': ('distributor','distitem', 'salestype', 'name', 'description', 'hna', 'hjp', 'pct_pm', 'pct_advdisc', 'priceuom', 'conversionsize', 'effective',)
        }),
        ('System Info', {
            'classes': ('collapsed',),
            'fields': ('status', 'remark', 'slug'),
            'description': 'System related information.',
        }),
    )

    dtype_mapping = {
        'DISTRIBUTOR': 'str',
        'DISTITEM': 'str',
        'SALESTYPE': 'str', 
        'HNA': 'str',
        'HJP': 'str',
        'PM': 'str',
        'ADVDISC': 'str',
        'PRICEUOM': 'str',
        'CONVERSIONSIZE': 'Int64',
        'NAME': 'str',
        'DESCRIPTION': 'str',
        'REMARK': 'str',
        'EFFECTIVE': 'str',
        'STATUS': 'str'
    }

    column_mapping = {} 

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

    def process_pandas_data(self, request, data):
        """
        Process the imported data and save it to the database.  
        """ 
        from decimal import Decimal, InvalidOperation
        from datetime import datetime
        
        def handle_blank(value):
            """Convert blank or NaN values to None for decimal fields."""
            if pd.isna(value) or value == '':
                return None
            return value

        def parse_decimal_safe(value):
            """Parse decimal values safely."""
            if pd.isna(value) or value == '' or value is None:
                return None
            try:
                return Decimal(str(value).strip())
            except (InvalidOperation, ValueError, AttributeError):
                return None

        def parse_date_safe(value):
            """Parse date values safely."""
            if pd.isna(value) or value == '' or value is None:
                return None
            
            # If it's already a date object
            if hasattr(value, 'date'):
                return value.date()
            
            # Try to parse string dates
            try:
                value_str = str(value).strip()
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(value_str, fmt).date()
                    except ValueError:
                        continue
                return None
            except:
                return None

        for _, row in data.iterrows():
            # Handle SalesType
            salestype_code = row['SALESTYPE'] if 'SALESTYPE' in row and pd.notna(row['SALESTYPE']) else None
            salestype = None
            if salestype_code and str(salestype_code).strip():
                try:
                    salestype = SalesType.objects.get(code=str(salestype_code).strip())
                except SalesType.DoesNotExist:
                    salestype = None

            # Handle Distributor  
            distributor_code = row['DISTRIBUTOR'] if 'DISTRIBUTOR' in row and pd.notna(row['DISTRIBUTOR']) else None
            distributor = None
            if distributor_code and str(distributor_code).strip():
                try:
                    distributor = Distributor.objects.get(code=str(distributor_code).strip())
                except Distributor.DoesNotExist:
                    distributor = None

            # Handle DistributorItem
            distitem_code = row['DISTITEM'] if 'DISTITEM' in row and pd.notna(row['DISTITEM']) else None
            distitem = None  
            if distitem_code and str(distitem_code).strip():
                try:
                    distitem = DistributorItem.objects.get(code=str(distitem_code).strip())
                except DistributorItem.DoesNotExist:
                    distitem = None

            # Handle Uom
            priceuom_code = row['PRICEUOM'] if 'PRICEUOM' in row and pd.notna(row['PRICEUOM']) else None
            priceuom = None  
            if priceuom_code and str(priceuom_code).strip():
                try:
                    priceuom = UoM.objects.get(code=str(priceuom_code).strip())
                except UoM.DoesNotExist:
                    priceuom = None

            # Handle other fields
            description = handle_blank(row['DESCRIPTION'] if 'DESCRIPTION' in row else None)
            remark = handle_blank(row['REMARK'] if 'REMARK' in row else None)
            hna = parse_decimal_safe(row['HNA'] if 'HNA' in row else None)
            hjp = parse_decimal_safe(row['HJP'] if 'HJP' in row else None)
            pct_pm = parse_decimal_safe(row['PM'] if 'PM' in row else None)
            pct_advdisc = parse_decimal_safe(row['ADVDISC'] if 'ADVDISC' in row else None)
            effective = parse_date_safe(row['EFFECTIVE'] if 'EFFECTIVE' in row else None)
            name = handle_blank(row['NAME'] if 'NAME' in row else '')
            status = handle_blank(row['STATUS'] if 'STATUS' in row else 'active')
            conversionsize = handle_blank(row['CONVERSIONSIZE'] if 'CONVERSIONSIZE' in row else 1)

            # Use ALL key fields to determine uniqueness - different prices/dates = different records
            obj, created = ItemPrice.objects.update_or_create(
                distributor=distributor,
                distitem=distitem,
                salestype=salestype,
                effective=effective,  # Include effective date in unique constraint
                hna=hna,             # Include HNA in unique constraint  
                hjp=hjp,             # Include HJP in unique constraint
                defaults={
                    'name': name,
                    'pct_pm': pct_pm,
                    'pct_advdisc': pct_advdisc,
                    'priceuom': priceuom,
                    'conversionsize': conversionsize,
                    'description': description,
                    'remark': remark,
                    'status': status,
                    'uby': request.user,  # Always set updated by
                    'uat': timezone.now(),  # Always set updated at
                }
            )
            
            # If it's a new record, set the created fields
            if created:
                obj.cby = request.user
                obj.cat = timezone.now()
                obj.save()
