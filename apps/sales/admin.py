from django.contrib import admin
from apps.sales.models.product import (
    Product,
    ProductPackage,
    ProductCategory,
    ProductSubgroup,
    ProductGroup,
)
from apps.sales.models.customer import (
    Customer,
    CustomerType,
    CustomerGroup,
    Outlet,
    OutletGroup,
    Satker,
)
from apps.sales.models.sales import (
    RepOffice,
    SalesType,
    RawMUSO,
    RawRNSO,
    RawLMSSO,
    RawKFSO,
    RawIGSO,
    RawPPSO,
    RawAPLSO,
    RawAPPSO,
    SellingOut,
    AnnualTarget,
    CycleTarget,
    ECatalog,
)
from apps.sales.models.territory import (
    SalesRegion,
    RegionProvince,
    SalesTeam,
    SalesArea,
    AreaRegency,
    SalesTerritory,
    TerritoryAssignment,
    KAMArea,
)
from apps.supplychain.models.distributions import Distributor, Branch, DistributorItem
from apps.supplychain.models.manufacturing import ManufacturingItem
from apps.base.models.entities import Company
from apps.base.models.locations import Village, District, Regency, Province
from apps.humancapital.models.business import Business
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.filters import StatusListFilter, DeletedListFilter, CustomerMap
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from decimal import Decimal, InvalidOperation
from django.db.models import Count, QuerySet
import os
import tempfile
import chardet
import dbfread
import re
from django.urls import path
from django.utils.text import slugify

# Pandas
from django import forms
import pandas as pd
import numpy as np
from django.shortcuts import redirect, render
from django.urls import reverse


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  PRODUCT MODULE                                            ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(Product)
class ProductAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "subgroup",
            "targetgroup",
            "category",
            "packaging",
            "business__initial",
            "owner",
        )
        + (
            "package",
            "size",
            "uom",
            "height",
            "length",
            "width",
            "weight",
            "box_per_palletac",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "subgroup",
                    "targetgroup",
                    "category",
                    "packaging",
                    "business",
                    "owner",
                    "description",
                )
            },
        ),
        (
            "Other Info",
            {
                "fields": (
                    "package",
                    "size",
                    "uom",
                    "height",
                    "length",
                    "width",
                    "weight",
                    "box_per_palletac",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "remark", "slug"),
                "description": "System related information.",
            },
        ),
    )
    has_pandas_import = True
    list_per_page = 1000
    dtype_mapping = {"code": "string"}

    # control the order of autocomplete results
    def get_search_results(self, request, queryset, search_term):
        qs, use_distinct = super().get_search_results(request, queryset, search_term)
        qs = qs.order_by("code", "name")  # or just "name"
        return qs, use_distinct

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
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
            if pd.isna(value) or value == "":
                return None
            return value

        for _, row in data.iterrows():
            subgroup_code = row["subgroup"]
            subgroup = ProductSubgroup.objects.get(code=subgroup_code)

            category_name = row["category"]
            category = ProductCategory.objects.get(name=category_name)

            # Process Package
            package_code = row["package"]
            package = None  # Default to None if blank
            if pd.notna(package_code) and package_code.strip() != "":
                try:
                    package = ProductPackage.objects.get(code=package_code)
                except ProductPackage.DoesNotExist:
                    package = None  # Handle as per your business logic

            business_code = row["business"]
            business = Business.objects.get(code=business_code)

            owner_code = row["owner"]
            owner = Company.objects.get(code=owner_code)

            # Handle Decimal Fields
            initial = handle_blank(row["initial"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            shortname = handle_blank(row["shortname"])
            targetgroup = handle_blank(row["targetgroup"])

            size = handle_blank(row["size"])
            height = handle_blank(row["height"])
            length = handle_blank(row["length"])
            width = handle_blank(row["width"])
            weight = handle_blank(row["weight"])
            box_per_palletac = handle_blank(row.get("box_per_palletac"))

            Product.objects.create(
                code=row["code"],
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                subgroup=subgroup,
                targetgroup=targetgroup,
                category=category,
                package=package,
                business=business,
                owner=owner,
                size=size,
                height=height,
                length=length,
                width=width,
                weight=weight,
                box_per_palletac=box_per_palletac,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductPackageAdmin                                 ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Package in Admin Site        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(ProductPackage)
class ProductPackageAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductCategoryAdmin                                ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Category in Admin Site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(ProductCategory)
class ProductCategoryAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductSubgroupAdmin                                ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Subgroup in Admin Site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(ProductSubgroup)
class ProductSubgroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("business", "group", "initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "business",
                    "name",
                    "initial",
                    "shortname",
                    "group",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )
    has_pandas_import = True
    dtype_mapping = {"code": "string"}

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        for _, row in data.iterrows():
            group_code = row["group"]
            group = ProductGroup.objects.get(code=group_code)

            business_code = row["business"]
            business = Business.objects.get(code=business_code)

            ProductSubgroup.objects.create(
                code=row["code"],
                business=business,
                name=row["name"],
                description=row["description"],
                remark=row["remark"],
                initial=row["initial"],
                shortname=row["shortname"],
                group=group,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ProductGroupAdmin                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Product Group in Admin Site          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/22-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(ProductGroup)
class ProductGroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("team", "business", "initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "description",
        "remark",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "team",
                    "business",
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )
    has_pandas_import = True
    dtype_mapping = {"code": "string"}

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, data):
        """
        Process the imported data and save it to the database.
        """
        for _, row in data.iterrows():

            business_code = row["business"]
            business = Business.objects.get(code=business_code)

            ProductGroup.objects.create(
                business=business,
                code=row["code"],
                name=row["name"],
                description=row["description"],
                remark=row["remark"],
                initial=row["initial"],
                shortname=row["shortname"],
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  CUSTOMER MODULE                                           ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CustomerAdmin                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Customer in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(Customer)
class CustomerAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "alias",
            "formername",
            "custtype",
            "repoffice",
            "station",
            "longitude",
            "latitude",
            "building",
            "street",
            "complex",
            "postcode",
        )
        + (
            "village",
            "district",
            "regency",
            "province",
            "edam_id",
            "subdist",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = ("name",)
    ordering = BaseModelAdmin.search_fields + (
        "code",
        "name",
        "initial",
        "shortname",
        "alias",
        "formername",
        "building",
        "street",
        "complex",
        "postcode",
    )
    list_per_page = 1000
    has_pandas_import = True
    autocomplete_fields = [
        "repoffice",
        "station",
        "village",
        "district",
        "regency",
        "province",
    ]
    dtype_mapping = {
        "code": "string",
        "village": "string",
        "district": "string",
        "regency": "string",
        "province": "string",
        "longitude": "string",
        "latitude": "string",
    }
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "custtype",
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "alias",
                    "formername",
                    "description",
                    "remark",
                    "repoffice",
                    "station",
                    "subdist",
                )
            },
        ),
        (
            "Address Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "building",
                    "street",
                    "complex",
                    "postcode",
                    "village",
                    "district",
                    "regency",
                    "province",
                    "longitude",
                    "latitude",
                ),
                "description": "Address and location information.",
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("edam_id", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    errors = []

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))

        if not obj:
            readonly.append("subdist")
        elif obj.custtype_id != 3:
            readonly.append("subdist")

        return readonly

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def get_village(self, village_name, district_code):
        """Find a village by name. If multiple results exist, filter by district if available."""
        if not village_name:  # ✅ If village is blank in CSV, return None
            return None

        try:
            # ✅ Step 1: Find villages by name (no district filter first)
            villages = Village.objects.filter(name__iexact=village_name)
            if villages.count() == 1:  # ✅ If exactly one match, return it
                return villages.first()

            elif villages.count() > 1:  # ✅ If multiple villages found
                if district_code:  # ✅ If district is provided, filter by district
                    filtered_villages = villages.filter(district__code=district_code)
                    if (
                        filtered_villages.count() == 1
                    ):  # ✅ If now only one remains, return it
                        return filtered_villages.first()

                # ✅ If district is blank or still multiple results, return None (store as NULL)
                self.errors.append(
                    f"Multiple villages found for '{village_name}', but district is blank. Using NULL."
                )
                return None

            else:  # ✅ No matches found
                self.errors.append(f"Village '{village_name}' not found. Using NULL.")
                return None

        except Exception as e:
            self.errors.append(f"Error finding village '{village_name}': {str(e)}")
            return None

    def process_pandas_data(self, request, data):
        """Process the imported data and save it to the database."""
        missing_data_rows = []  # List to store rows with missing foreign keys

        def handle_blank(value, default="-", is_fk=False, is_decimal=False):
            """Convert blank or NaN values to None (for FK) or an empty string (for text)."""
            if (
                value is None
                or pd.isna(value)
                or isinstance(value, pd._libs.missing.NAType)
                or value in ["nan", "NaN", ""]
            ):  # ✅ Check for NaN or 'nan' strings
                return (
                    None if is_fk or is_decimal else ""
                )  # ✅ Return None for FK, empty string for others

            if isinstance(value, float) and pd.isna(value):  # ✅ Handle float NaNs
                return None if is_fk else ""

            if is_decimal:
                value = str(value).strip()  # ✅ Remove extra spaces
                if value == "":  # ✅ If still blank, return None
                    return None
                try:
                    return Decimal(value)
                except InvalidOperation:
                    print(
                        f"⚠️ Invalid decimal: {value}, setting to None"
                    )  # Debugging print
                    return None  # ✅ If invalid, return None instead of crashing
            return (
                str(value).strip() if isinstance(value, str) else value
            )  # ✅ Convert to string for consistency

        def get_fk(model, field_name, value, extra_filter=None):
            """Get foreign key object safely, return None if not found."""
            if not value:
                return None
            filter_kwargs = {field_name: value}
            if extra_filter:  # Add extra filtering if needed (e.g., district name)
                filter_kwargs.update(extra_filter)

            try:
                return model.objects.get(**filter_kwargs)
            except model.MultipleObjectsReturned:
                error_message = f"Multiple {model.__name__} found for '{value}'. Trying to refine search..."
                self.errors.append(error_message)
                return None  # Don't fail; just leave it blank
            except model.DoesNotExist:
                error_message = f"Row {index}: FK Not Found: {model.__name__} where {field_name} = '{value}'"
                self.errors.append(error_message)
                return None  # Don't skip the row; just set FK to None

        def generate_code(custtype):
            """
            Generate a unique customer code using custtype and an incrementing number.
            """
            last_customer = (
                Customer.objects.filter(code__startswith=custtype)
                .order_by("-code")
                .first()
            )
            last_number = 0  # Default start if no previous codes exist
            if last_customer and last_customer.code:
                numeric_part = last_customer.code[len(custtype) :]  # Extract number
                if numeric_part.isdigit():
                    last_number = int(numeric_part)
                else:
                    print(
                        f"Warning: Unexpected code format '{last_customer.code}', resetting numbering."
                    )
            new_number = last_number + 1
            code = f"{custtype}{new_number:08d}"  # Ensure 8 digits
            # Final validation before saving
            if len(code) > 10:
                raise ValueError(f"Generated code '{code}' exceeds 10 characters!")
            return code

        for index, row in data.iterrows():
            try:
                row_errors = []  # ✅ Store errors for this row
                # ✅ Get the logged-in user for `uby`
                user_by = request.user if request.user.is_authenticated else None

                # Process Code
                # Get custtype and ensure it's valid
                custtype_code = handle_blank(row.get("custtype"), default=None)
                if not custtype_code:
                    self.errors.append(f"Row {index}: Missing Customer Type")
                    continue
                # Convert custtype_code to CustomerType instance
                try:
                    custtype = CustomerType.objects.get(code=custtype_code.strip())
                except CustomerType.DoesNotExist:
                    self.errors.append(
                        f"Row {index}: Customer Type '{custtype_code}' not found"
                    )
                    row_errors.append(f"Customer Type '{custtype_code}' not found")
                    custtype = None

                # Safely get FK fields
                province_value = handle_blank(row.get("province"), is_fk=True)
                province = get_fk(Province, "code", province_value)
                province_csv_value = handle_blank(
                    row.get("province"), is_fk=True
                )  # ✅ Ensures row.get('province') is not `pd.NA`
                if (
                    province is None and province_csv_value is not None
                ):  # ✅ No more `pd.NA` issue
                    row_errors.append(f"Province '{province_csv_value}' not found")

                regency_value = handle_blank(row.get("regency"), is_fk=True)
                regency = get_fk(Regency, "code", regency_value)
                regency_csv_value = handle_blank(row.get("regency"), is_fk=True)
                if regency is None and regency_csv_value is not None:
                    row_errors.append(f"Regency '{regency_csv_value}' not found")

                district_value = handle_blank(row.get("district"), is_fk=True)
                district = get_fk(District, "code", district_value)
                district_csv_value = handle_blank(row.get("district"), is_fk=True)
                if district is None and district_csv_value is not None:
                    row_errors.append(f"District '{district_csv_value}' not found")

                village_name = (handle_blank(row.get("village"), is_fk=True),)
                village = self.get_village(
                    village_name, district.code if district else None
                )
                village_csv_value = handle_blank(row.get("village"), is_fk=True)

                if isinstance(village, tuple):  # ✅ Fix if village is a tuple
                    print(
                        f"⚠️ Row {index+1} - Village is tuple {village}, extracting first element"
                    )
                    village = village[0]  # ✅ Extract first element if tuple

                if village is None and village_csv_value is not None:
                    row_errors.append(f"Village '{village_csv_value}' not found")

                repoffice_value = handle_blank(row.get("repoffice"), is_fk=True)
                repoffice = get_fk(RepOffice, "name", repoffice_value)
                repoffice_csv_value = handle_blank(row.get("repoffice"), is_fk=True)
                if repoffice is None and repoffice_csv_value is not None:
                    row_errors.append(f"RepOffice '{repoffice_csv_value}' not found")

                station_value = handle_blank(row.get("station"), is_fk=True)
                station = get_fk(RepOffice, "name", station_value)
                station_csv_value = handle_blank(row.get("station"), is_fk=True)
                if station is None and station_csv_value is not None:
                    row_errors.append(f"Station '{station_csv_value}' not found")

                longitude = handle_blank(
                    row.get("longitude"), default=None, is_decimal=True
                )
                latitude = handle_blank(
                    row.get("latitude"), default=None, is_decimal=True
                )

                # Capture rows with missing foreign keys
                # ✅ Add Row to `missing_data_rows` If It Has Errors
                if row_errors:
                    row_dict = row.to_dict()
                    row_dict["error_description"] = "; ".join(
                        row_errors
                    )  # ✅ Add error messages column
                    missing_data_rows.append(row_dict)

                unique_identifier = {
                    "name": row["name"],
                    "custtype": custtype,
                    "province": province,
                    "regency": regency,
                    "district": district,
                }

                # Check if customer already exists using unique identifier
                customer = Customer.objects.filter(**unique_identifier).first()
                if customer:
                    # ✅ Customer exists → Update existing record
                    Customer.objects.filter(id=customer.id).update(
                        description=handle_blank(row.get("description")),
                        remark=handle_blank(row.get("remark")),
                        initial=handle_blank(row.get("initial")),
                        shortname=handle_blank(row.get("shortname")),
                        alias=handle_blank(row.get("alias")),
                        formername=handle_blank(row.get("formername")),
                        repoffice=repoffice,
                        station=station,
                        longitude=longitude,
                        latitude=latitude,
                        building=handle_blank(row.get("building")),
                        street=handle_blank(row.get("street")),
                        complex=handle_blank(row.get("complex")),
                        postcode=handle_blank(row.get("postcode")),
                        village=village,
                        edam_id=handle_blank(row.get("edam_id"), default=None),
                        status=row.get("status"),
                        uby=user_by,  # Set Updated By
                        uat=now(),  # Set Updated At
                    )
                else:
                    # ✅ New Customer → Generate Code & Create New Record
                    code = generate_code(custtype.code)
                    Customer.objects.create(
                        code=code,
                        name=row["name"],
                        custtype=custtype,
                        province=province,
                        regency=regency,
                        district=district,
                        repoffice=repoffice,
                        station=station,
                        longitude=longitude,
                        latitude=latitude,
                        building=handle_blank(row.get("building")),
                        street=handle_blank(row.get("street")),
                        complex=handle_blank(row.get("complex")),
                        postcode=handle_blank(row.get("postcode")),
                        village=village,
                        edam_id=handle_blank(row.get("edam_id"), default=None),
                        status=row.get("status"),
                        description=handle_blank(row.get("description")),
                        remark=handle_blank(row.get("remark")),
                        initial=handle_blank(row.get("initial")),
                        shortname=handle_blank(row.get("shortname")),
                        alias=handle_blank(row.get("alias")),
                        formername=handle_blank(row.get("formername")),
                        cby=user_by,  # Set Created By
                        cat=now(),  # Set Created At
                    )
            except Exception as e:
                error_message = f"Row {index}: Unexpected error - {str(e)}"
                self.errors.append(error_message)

        # ✅ Save missing data to session for later download
        if missing_data_rows:
            request.session["missing_data"] = missing_data_rows
            messages.warning(
                request,
                mark_safe(
                    "Some rows has missing data. <a href='/base/download_missing_data/' target='_blank'>Download Missing Data</a>"
                ),
            )
            return JsonResponse(
                {"download_csv": True}
            )  # ✅ Signal frontend to download CSV

        # Show success or error messages in Django Admin
        if self.errors:
            messages.error(
                request,
                f"Import completed with {len(self.errors)} errors. Check logs for details.",
            )
            for error in self.errors:
                messages.error(request, error)
        else:
            messages.success(request, "Import completed successfully with no errors.")

        return JsonResponse({"download_csv": False})  # ✅ No CSV, just show messages


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CustomerTypeAdmin                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Customer Type in Admin Site          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(CustomerType)
class CustomerTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CustomerGroupAdmin                                  ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Customer Group in Admin Site         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(CustomerGroup)
class CustomerGroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "ctype")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "ctype",
    )
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
        extra_context["has_pandas_import"] = self.has_pandas_import
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
            if pd.isna(value) or value == "":
                return None
            return value

        for _, row in data.iterrows():
            # Handle Blank Fields
            code = handle_blank(row["code"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            initial = handle_blank(row["initial"])
            shortname = handle_blank(row["shortname"])
            ctype = handle_blank(row["ctype"])

            CustomerGroup.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                ctype=ctype,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  OUTLET MODULE                                             ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: OutletAdmin                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Outlet in Admin Site                 ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(Outlet)
class OutletAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + (
            "code",
            "code1",
            "code2",
        )
        + BaseModelAdmin.list_display_name
        + (
            "distributor",
            "branch",
            "outletgroup",
            "custtype",
            "address",
            "customer",
            "edam_id",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "code",
            "code1",
            "code2",
            "custtype__name",
            "distributor__code",
            "branch__code",
            "outletgroup__name",
        )
        + (
            "address",
            "customer__name",
            "edam_id",
        )
    )
    list_per_page = 1000
    has_pandas_import = True
    autocomplete_fields = ["outletgroup", "customer"]
    dtype_mapping = {
        "code": "string",
        "code1": "string",
        "code2": "string",
        "outletgroup": "string",
    }
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
        CustomerMap,
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "custtype",
                    "distributor",
                    "branch",
                    "code",
                    "code1",
                    "code2",
                    "name",
                    "outletgroup",
                    "address",
                    "description",
                    "remark",
                    "customer",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("edam_id", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    errors = []

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def process_pandas_data(self, request, data):
        """Process the imported data and save it to the database."""
        missing_data_rows = []  # List to store rows with missing foreign keys

        def handle_blank(value, default="-", is_fk=False, is_decimal=False):
            """Convert blank or NaN values to None (for FK) or an empty string (for text)."""
            if (
                value is None
                or pd.isna(value)
                or isinstance(value, pd._libs.missing.NAType)
                or value in ["nan", "NaN", ""]
            ):  # ✅ Check for NaN or 'nan' strings
                return (
                    None if is_fk or is_decimal else ""
                )  # ✅ Return None for FK, empty string for others

            if isinstance(value, float) and pd.isna(value):  # ✅ Handle float NaNs
                return None if is_fk else ""

            if is_decimal:
                value = str(value).strip()  # ✅ Remove extra spaces
                if value == "":  # ✅ If still blank, return None
                    return None
                try:
                    return Decimal(value)
                except InvalidOperation:
                    print(
                        f"⚠️ Invalid decimal: {value}, setting to None"
                    )  # Debugging print
                    return None  # ✅ If invalid, return None instead of crashing
            return (
                str(value).strip() if isinstance(value, str) else value
            )  # ✅ Convert to string for consistency

        def get_fk(model, field_name, value, extra_filter=None):
            """Get foreign key object safely, return None if not found."""
            if not value:
                return None
            filter_kwargs = {field_name: value}
            if extra_filter:  # Add extra filtering if needed (e.g., district name)
                filter_kwargs.update(extra_filter)

            try:
                return model.objects.get(**filter_kwargs)
            except model.MultipleObjectsReturned:
                error_message = f"Multiple {model.__name__} found for '{value}'. Trying to refine search..."
                self.errors.append(error_message)
                return None  # Don't fail; just leave it blank
            except model.DoesNotExist:
                error_message = f"Row {index}: FK Not Found: {model.__name__} where {field_name} = '{value}'"
                self.errors.append(error_message)
                return None  # Don't skip the row; just set FK to None

        def generate_code(custtype):
            """
            Generate a unique customer code using custtype and an incrementing number.
            """
            last_outlet = (
                Outlet.objects.filter(code__startswith=f"OT{custtype}")
                .order_by("-code")
                .first()
            )
            last_number = 0  # Default start if no previous codes exist
            if last_outlet and last_outlet.code:
                numeric_part = last_outlet.code[
                    len(f"OT{custtype}") :
                ]  # Extract number
                if numeric_part.isdigit():
                    last_number = int(numeric_part)
                else:
                    print(
                        f"Warning: Unexpected code format '{last_outlet.code}', resetting numbering."
                    )
            new_number = last_number + 1
            code = f"OT{custtype}{new_number:08d}"  # Ensure 8 digits
            # Final validation before saving
            if len(code) > 15:
                raise ValueError(f"Generated code '{code}' exceeds 15 characters!")
            return code

        for index, row in data.iterrows():
            try:
                row_errors = []  # ✅ Store errors for this row
                # ✅ Get the logged-in user for `uby`
                user_by = request.user if request.user.is_authenticated else None

                # Process Code
                # Get custtype and ensure it's valid
                custtype_code = handle_blank(row.get("custtype"), default=None)
                if not custtype_code:
                    self.errors.append(f"Row {index}: Missing Customer Type")
                    continue
                # Convert custtype_code to CustomerType instance
                try:
                    custtype = CustomerType.objects.get(code=custtype_code.strip())
                except CustomerType.DoesNotExist:
                    self.errors.append(
                        f"Row {index}: Customer Type '{custtype_code}' not found"
                    )
                    row_errors.append(f"Customer Type '{custtype_code}' not found")
                    custtype = None

                # Safely get FK fields
                distributor_value = handle_blank(row.get("distributor"), is_fk=True)
                distributor = get_fk(Distributor, "code", distributor_value)
                distributor_csv_value = handle_blank(row.get("distributor"), is_fk=True)
                if distributor is None and distributor_csv_value is not None:
                    row_errors.append(
                        f"Distributor '{distributor_csv_value}' not found"
                    )

                branch_value = handle_blank(row.get("branch"), is_fk=True)
                branch = get_fk(
                    Branch,
                    "code",
                    branch_value,
                    extra_filter={"status": 1, "distributor__code": distributor_value},
                )
                branch_csv_value = handle_blank(row.get("branch"), is_fk=True)
                if branch is None and branch_csv_value is not None:
                    row_errors.append(f"Branch '{branch_csv_value}' not found")

                outletgroup_value = handle_blank(row.get("outletgroup"), is_fk=True)
                outletgroup = get_fk(
                    OutletGroup,
                    "code",
                    outletgroup_value,
                    extra_filter={"status": 1, "distributor__code": distributor_value},
                )
                outletgroup_csv_value = handle_blank(row.get("outletgroup"), is_fk=True)
                if outletgroup is None and outletgroup_csv_value is not None:
                    row_errors.append(
                        f"Outlet Group '{outletgroup_csv_value}' not found"
                    )

                customer_value = handle_blank(row.get("customer"), is_fk=True)
                customer = get_fk(Customer, "edam_id", customer_value)
                customer_csv_value = handle_blank(row.get("customer"), is_fk=True)
                if customer is None and customer_csv_value is not None:
                    row_errors.append(f"Customer '{customer_csv_value}' not found")

                # Capture rows with missing foreign keys
                # ✅ Add Row to `missing_data_rows` If It Has Errors
                if row_errors:
                    row_dict = row.to_dict()
                    row_dict["error_description"] = "; ".join(
                        row_errors
                    )  # ✅ Add error messages column
                    missing_data_rows.append(row_dict)

                # Normalize `code1` to ensure it's a string
                code1 = row.get("code1")
                if isinstance(code1, (tuple, list)):
                    code1 = code1[
                        0
                    ]  # Extract first value if mistakenly stored as a tuple
                if code1 is not None:
                    code1 = str(code1).strip()  # Convert to string & remove spaces

                unique_identifier = {
                    "name": (
                        row["name"].strip()
                        if isinstance(row["name"], str)
                        else row["name"]
                    ),
                    "custtype": custtype,
                    "distributor": distributor,
                    "branch": branch,
                    "code1": code1,
                }

                # Remove empty values
                unique_identifier = {
                    k: v if v not in [None, ""] else None
                    for k, v in unique_identifier.items()
                }

                # Check if customer already exists using unique identifier
                outlet = Outlet.objects.filter(**unique_identifier).first()

                if outlet:
                    # ✅ Customer exists → Update existing record
                    Outlet.objects.filter(id=outlet.id).update(
                        outletgroup=outletgroup,
                        code2=handle_blank(row.get("code2")),
                        description=handle_blank(row.get("description")),
                        remark=handle_blank(row.get("remark")),
                        address=handle_blank(row.get("address")),
                        customer=customer,
                        edam_id=handle_blank(row.get("edam_id"), default=None),
                        status=row.get("status"),
                        uby=user_by,  # Set Updated By
                        uat=now(),  # Set Updated At
                    )
                else:
                    # ✅ New Customer → Generate Code & Create New Record
                    code = generate_code(custtype.code)
                    Outlet.objects.create(
                        code=code,
                        code1=handle_blank(row.get("code1")),
                        code2=handle_blank(row.get("code2")),
                        custtype=custtype,
                        distributor=distributor,
                        branch=branch,
                        name=row["name"],
                        outletgroup=outletgroup,
                        address=handle_blank(row.get("address")),
                        customer=customer,
                        edam_id=handle_blank(row.get("edam_id"), default=None),
                        status=row.get("status"),
                        description=handle_blank(row.get("description")),
                        remark=handle_blank(row.get("remark")),
                        cby=user_by,  # Set Created By
                        cat=now(),  # Set Created At
                    )
            except Exception as e:
                error_message = f"Row {index}: Unexpected error - {str(e)}"
                self.errors.append(error_message)

        # ✅ Save missing data to session for later download
        if missing_data_rows:
            request.session["missing_data"] = missing_data_rows
            messages.warning(
                request,
                mark_safe(
                    "Some rows has missing data. <a href='/base/download_missing_data/' target='_blank'>Download Missing Data</a>"
                ),
            )
            return JsonResponse(
                {"download_csv": True}
            )  # ✅ Signal frontend to download CSV

        # Show success or error messages in Django Admin
        if self.errors:
            messages.error(
                request,
                f"Import completed with {len(self.errors)} errors. Check logs for details.",
            )
            for error in self.errors:
                messages.error(request, error)
        else:
            messages.success(request, "Import completed successfully with no errors.")

        return JsonResponse({"download_csv": False})  # ✅ No CSV, just show messages


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: OutletGroupAdmin                                    ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Outlet Group in Admin Site           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(OutletGroup)
class OutletGroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "distributor")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "distcode",
        "initial",
        "shortname",
        "type",
        "distributor__code",
    )
    list_per_page = 1000
    has_pandas_import = True
    fields = ["code", "name", "initial", "description", "remark", "distcode", "slug"]
    dtype_mapping = {"code": "string"}

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
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
            if pd.isna(value) or value == "":
                return None
            return value

        for _, row in data.iterrows():
            # Process Distributor
            distributor_code = row["distributor"]
            distributor = None  # Default to None if blank
            if pd.notna(distributor_code) and distributor_code.strip() != "":
                try:
                    distributor = Distributor.objects.get(code=distributor_code)
                except Distributor.DoesNotExist:
                    distributor = None  # Handle as per your business logic

            # Handle Blank Fields
            code = handle_blank(row["code"])
            distcode = handle_blank(row["distcode"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            initial = handle_blank(row["initial"])
            shortname = handle_blank(row["shortname"])

            OutletGroup.objects.create(
                code=code,
                distcode=distcode,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                distributor=distributor,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  SALES MODULE                                              ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SellingOutAdmin                                     ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering SellingOut in Admin Site             ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/30-2025 by Noval                             ║
# ║  Updates: Jul/3-2025 by Noval                              ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(SellingOut)
class SellingOutAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "raw_id",
            "invoice_date",
            "company_id",
            "branch_id",
            "distributor_id",
            "outlet_id",
            "item_id",
            "invoice_number",
            "qty",
            "bonusqty",
            "bonusvalue",
            "grossvalue",
            "discvalue",
            "netvalue",
            "prsnbp",
            "prsnbmp",
            "isbonus",
            "pricecode",
            "hjpprice",
            "hjpvalue",
            "so",
            "soo",
            "uom",
            "closed",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True
    ordering = ("-invoice_date",)

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "raw_id",
        "invoice_date",
        "company_id",
        "branch_id",
        "distributor_id",
        "outlet_id",
        "item_id",
        "invoice_number",
        "qty",
        "bonusqty",
        "bonusvalue",
        "grossvalue",
        "discvalue",
        "netvalue",
        "prsnbp",
        "prsnbmp",
        "isbonus",
        "pricecode",
        "hjpprice",
        "hjpvalue",
        "so",
        "soo",
        "closed",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawMUSOAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawMUSO in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/16-2025 by Noval                             ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawMUSO)
class RawMUSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "whse",
            "hrdok",
            "nodokjdi",
            "no_order",
            "area",
            "kodepos",
            "gruplang",
            "kodelang",
            "kdcust",
            "nmlang",
            "almtlang",
            "kodesalur",
            "kodeprod",
            "nmprod",
        )
        + (
            "principle",
            "klasprod",
            "nmklas1",
            "nmklas2",
            "banyak",
            "hna",
            "harga",
            "tharga",
            "thna",
            "banys",
            "ehna",
            "prsnpot",
            "pharga",
            "prsnbp",
            "prsnbmp",
        )
        + ("mom", "nobat", "dun", "idpkt", "code")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    list_per_page = 1000
    has_pandas_import = True
    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "code",
            "whse",
            "hrdok",
            "nodokjdi",
            "no_order",
            "area",
            "kodepos",
            "gruplang",
            "kodelang",
            "kdcust",
            "nmlang",
            "almtlang",
        )
        + (
            "kodesalur",
            "kodeprod",
            "nmprod",
            "principle__name",
            "klasprod",
            "nmklas1",
            "nmklas2",
        )
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "whse",
                    "hrdok",
                    "nodokjdi",
                    "gruplang",
                    "kodelang",
                    "kdcust",
                    "nmlang",
                    "kodeprod",
                    "nmprod",
                    "banyak",
                    "banys",
                    "tharga",
                    "pharga",
                    "thna",
                )
            },
        ),
        (
            "Product Info",
            {
                "classes": ("collapsed",),
                "fields": ("principle", "klasprod", "nmklas1", "nmklas2", "kodesalur"),
                "description": "Product information.",
            },
        ),
        (
            "Finance Info",
            {
                "classes": ("collapsed",),
                "fields": ("hna", "harga", "ehna", "prsnpot", "prsnbp", "prsnbmp"),
                "description": "Product information.",
            },
        ),
        (
            "Other Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "no_order",
                    "area",
                    "kodepos",
                    "almtlang",
                    "mom",
                    "nobat",
                    "dun",
                    "idpkt",
                ),
                "description": "Other information.",
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "whse": "string",
        "no_order": "string",
        "nodokjdi": "string",
        "hrdok": "string",
        "area": "string",
        "kodepos": "string",
        "gruplang": "string",
        "kodelang": "string",
        "kdcust": "string",
        "nmlang": "string",
        "almtlang": "string",
        "kodesalur": "string",
        "kodeprod": "string",
        "nmprod": "string",
        "klasprod": "string",
        "nmklas1": "string",
        "nmklas2": "string",
        "banyak": "float",
        "hna": "float",
        "harga": "float",
        "tharga": "float",
        "thna": "float",
        "banys": "float",
        "ehna": "float",
        "pharga": "float",
        "mom": "string",
        "nobat": "string",
        "dun": "string",
        "idpkt": "string",
        "prsnpot": "float",
        "prsnbp": "float",
        "prsnbmp": "float",
    }

    column_mapping = {  # Map external column names to internal field names
        "WHSE": "whse",
        "NO_ORDER": "no_order",
        "NODOKJDI": "nodokjdi",
        "HRDOK": "hrdok",
        "AREA": "area",
        "KODEPOS": "kodepos",
        "GRUPLANG": "gruplang",
        "KODELANG": "kodelang",
        "KDCUST": "kdcust",
        "NMLANG": "nmlang",
        "ALMTLANG": "almtlang",
        "KODESALUR": "kodesalur",
        "KODEPROD": "kodeprod",
        "NMPROD": "nmprod",
        "KLASPROD": "klasprod",
        "NMKLAS1": "nmklas1",
        "NMKLAS2": "nmklas2",
        "BANYAK": "banyak",
        "HNA": "hna",
        "HARGA": "harga",
        "THARGA": "tharga",
        "THNA": "thna",
        "BANYS": "banys",
        "EHNA": "ehna",
        "PRSNPOT": "prsnpot",
        "PHARGA": "pharga",
        "PRSNBP": "prsnbp",
        "PRSNBMP": "prsnbmp",
        "MOM": "mom",
        "NOBAT": "nobat",
        "DUN": "dun",
        "IDPKT": "idpkt",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # duplicates = (
        #    self.model.objects.values("code")  # ✅ Check duplicates in the entire database
        #    .annotate(count=Count("id"))
        #    .filter(count__gt=1)
        # )

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        """Add a custom pandas import URL that only works for RawMUSOAdmin."""
        opts = self.model._meta
        custom_urls = [
            path(
                "pandas-import/",
                self.admin_site.admin_view(self.pandas_import),  # ✅ Custom Import
                name=f"{opts.app_label}_{opts.model_name}_pandas_import",
            ),
        ]
        return custom_urls + super().get_urls()

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def generate_code(
        self, hrdok, whse, nodokjdi, kodeprod, nobat, hna, harga, banyak, banys, mom
    ):
        """
        Generate a unique customer code using custtype and an incrementing number.
        """
        whse_str = str(whse).strip() if whse else ""
        if whse_str.isdigit():
            whse_str = f"{int(whse_str):03d}"

        nodokjdi_str = str(nodokjdi).strip() if nodokjdi else ""
        if nodokjdi_str.isdigit():
            nodokjdi_str = f"{int(nodokjdi_str):07d}"

        mom_str = str(mom).strip() if mom else "NA"
        if mom_str.isdigit():
            mom_str = f"{int(mom_str):03d}"

        hna_value = str(hna) if hna not in [None, "", "NULL"] else "0"
        harga_value = str(harga) if harga not in [None, "", "NULL"] else "0"
        banys_value = (
            str(banys) if banys not in [None, "", "NULL"] else "0"
        )  # ✅ Ensure banys is always "0"

        code = f"{hrdok}-{whse_str}-{nodokjdi_str[-7:]}-{kodeprod}-{nobat}-{hna_value}-{harga_value}-{banyak}-{banys_value}-{mom_str}"

        return code

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=dtype_mapping)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data.columns = data.columns.str.upper().str.strip()
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null

                # Keep only expected columns
                data = data[expected_columns]
                # Choose Upload Mode: Normal (row-by-row) or Batch Processing
                use_batch = request.POST.get(
                    "use_batch", False
                )  # ✅ Get user choice from form
                if use_batch:
                    self.message_user(
                        request, "Batch Upload Mode Enabled. Processing data..."
                    )
                    response = self.process_pandas_data_batch(
                        request, data
                    )  # ✅ Use batch processing
                else:
                    self.message_user(
                        request, "Row-by-Row Upload Mode Enabled. Processing data..."
                    )
                    response = self.process_pandas_data(
                        request, data
                    )  # ✅ Use row-by-row

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Normalize text values so regex never crashes on non-string input."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""

        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", "ignore")
            except Exception:
                value = value.decode("latin-1", "ignore")

        value = str(value)
        try:
            cleaned = re.sub(r"[^\x20-\x7E]", "", value)
        except TypeError:
            cleaned = re.sub(r"[^\x20-\x7E]", "", str(value))
        return cleaned.strip()

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None

        # Step 1: Process Data to meet requirements
        data["whse"] = data["whse"].astype(str).str.zfill(3)
        data["nodokjdi"] = data["nodokjdi"].astype(str)
        data["mom"] = (
            data["mom"]
            .fillna("NA")
            .astype(str)
            .str.strip()
            .replace("nan", "NA")
            .replace("None", "NA")
        )
        data["klasprod"] = (
            data["klasprod"]
            .astype(str)
            .where(pd.notna(data["klasprod"]), "")
            .str.zfill(9)
        )
        data["principle_id"] = (
            data["klasprod"].fillna("").astype(str).str[:3].str[-1:].astype(int)
        )

        num_as_str_fields = [
            "hrdok",
            "no_order",
            "area",
            "kodepos",
            "gruplang",
            "kodelang",
            "kodesalur",
        ]
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        if "kodepos" in data.columns:
            if pd.api.types.is_numeric_dtype(data["kodepos"]):
                data["kodepos"] = data["kodepos"].astype(int).astype(str).str[-5:]
            else:
                data["kodepos"] = (
                    data["kodepos"].fillna("").astype(str).str.strip().str[-5:]
                )

        decimal_fields = [
            "banyak",
            "banys",
            "hna",
            "harga",
            "thna",
            "tharga",
            "ehna",
            "prsnpot",
            "pharga",
            "prsnbp",
            "prsnbmp",
        ]
        # data[decimal_fields] = data[decimal_fields].fillna(0).astype(float)
        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        string_columns = [
            "nmlang",
            "almtlang",
            "kodesalur",
            "nmprod",
            "nmklas1",
            "nmklas2",
            "nobat",
            "dun",
            "idpkt",
        ]
        for col in string_columns:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["hrdok"].astype(str)
            + "-"
            + data["whse"].astype(str)
            + "-"
            + data["nodokjdi"].astype(str).str[-7:]
            + "-"
            + data["kodeprod"].astype(str)
            + "-"
            + data["nobat"].astype(str)
            + "-"
            + data["hna"].astype(int).astype(str)
            + "-"
            + data["harga"].astype(int).astype(str)
            + "-"
            + data["banyak"].astype(int).astype(str)
            + "-"
            + data["banys"].astype(int).astype(str)
            + "-"
            + data["mom"].astype(str)
        )
        data["name"] = (
            data["hrdok"].astype(str)
            + data["whse"].astype(str)
            + "-"
            + data["nodokjdi"].astype(str)
            + "-"
            + data["kodeprod"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )  # modify 2025-07-02

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawMUSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            for chunk in self.iter_chunks(new_records_dict, batch_size):
                bulk_insert_objs = [
                    RawMUSO(
                        code=row.get("code", ""),
                        principle_id=(
                            row.get("principle_id") if row.get("principle_id") else None
                        ),
                        slug=row.get("slug", ""),
                        name=row.get("name", ""),
                        hrdok=row.get("hrdok", ""),
                        whse=row.get("whse", ""),
                        nodokjdi=row.get("nodokjdi", ""),
                        kodeprod=row.get("kodeprod", ""),
                        banyak=row.get("banyak"),
                        banys=row.get("banys"),
                        hna=row.get("hna"),
                        harga=row.get("harga"),
                        mom=row.get("mom", "NA"),
                        description=row.get("description", ""),
                        remark=row.get("remark", ""),
                        no_order=row.get("no_order", ""),
                        area=row.get("area", ""),
                        kodepos=row.get("kodepos", ""),
                        gruplang=row.get("gruplang", ""),
                        kodelang=row.get("kodelang", ""),
                        kdcust=row.get("kdcust", ""),
                        nmlang=row.get("nmlang", ""),
                        almtlang=row.get("almtlang", ""),
                        kodesalur=row.get("kodesalur", ""),
                        nmprod=row.get("nmprod", ""),
                        klasprod=row.get("klasprod", ""),
                        nmklas1=row.get("nmklas1", ""),
                        nmklas2=row.get("nmklas2", ""),
                        thna=row.get("thna"),
                        tharga=row.get("tharga"),
                        ehna=row.get("ehna"),
                        prsnpot=row.get("prsnpot"),
                        pharga=row.get("pharga"),
                        prsnbp=row.get("prsnbp"),
                        prsnbmp=row.get("prsnbmp"),
                        nobat=row.get("nobat", ""),
                        dun=row.get("dun", ""),
                        idpkt=row.get("idpkt", ""),
                        status=1,
                        cby=user_by,
                        cat=now(),
                    )
                    for row in chunk
                ]
                RawMUSO.objects.bulk_create(
                    bulk_insert_objs, batch_size=min(batch_size, len(bulk_insert_objs))
                )

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawMUSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            update_fields = [
                "description",
                "remark",
                "no_order",
                "area",
                "kodepos",
                "gruplang",
                "kodelang",
                "kdcust",
                "nmlang",
                "almtlang",
                "kodesalur",
                "nmprod",
                "klasprod",
                "nmklas1",
                "nmklas2",
                "thna",
                "tharga",
                "ehna",
                "prsnpot",
                "pharga",
                "prsnbp",
                "prsnbmp",
                "dun",
                "idpkt",
                "status",
                "uby",
                "uat",
            ]
            for chunk in self.iter_chunks(existing_records_dict, batch_size):
                bulk_update_objs = [
                    RawMUSO(
                        id=existing_code_to_id.get(row["code"]),
                        principle_id=(
                            row.get("principle_id") if row.get("principle_id") else None
                        ),
                        description=row.get("description", ""),
                        remark=row.get("remark", ""),
                        no_order=row.get("no_order", ""),
                        area=row.get("area", ""),
                        kodepos=row.get("kodepos", ""),
                        gruplang=row.get("gruplang", ""),
                        kodelang=row.get("kodelang", ""),
                        kdcust=row.get("kdcust", ""),
                        nmlang=row.get("nmlang", ""),
                        almtlang=row.get("almtlang", ""),
                        kodesalur=row.get("kodesalur", ""),
                        nmprod=row.get("nmprod", ""),
                        klasprod=row.get("klasprod", ""),
                        nmklas1=row.get("nmklas1", ""),
                        nmklas2=row.get("nmklas2", ""),
                        thna=row.get("thna"),
                        tharga=row.get("tharga"),
                        ehna=row.get("ehna"),
                        prsnpot=row.get("prsnpot"),
                        pharga=row.get("pharga"),
                        prsnbp=row.get("prsnbp"),
                        prsnbmp=row.get("prsnbmp"),
                        dun=row.get("dun", ""),
                        idpkt=row.get("idpkt", ""),
                        status=1,
                        uby=user_by,
                        uat=now(),
                    )
                    for row in chunk
                    if row["code"] in existing_code_to_id
                ]
                if bulk_update_objs:
                    RawMUSO.objects.bulk_update(
                        bulk_update_objs,
                        update_fields,
                        batch_size=min(batch_size, len(bulk_update_objs)),
                    )

    def iter_chunks(self, items, size):
        """Yield list chunks without loading everything into memory at once."""
        total = len(items)
        for start in range(0, total, max(size, 1)):
            yield items[start : start + max(size, 1)]

    def process_pandas_data(self, request, data):
        """Process the imported data and save it to the database."""
        missing_data_rows = []  # List to store rows with missing foreign keys
        total_saved = 0
        for index, row in data.iterrows():
            try:
                row_errors = []  # ✅ Store errors for this row
                # ✅ Get the logged-in user for `uby`
                user_by = request.user if request.user.is_authenticated else None
                description = self.handle_data(
                    row.get("description"), expected_type="string"
                )
                remark = self.handle_data(row.get("remark"), expected_type="string")
                no_order = self.handle_data(
                    row.get("no_order", ""), expected_type="string"
                )
                area = self.handle_data(row.get("area"), expected_type="string")
                kodepos = self.handle_data(
                    row.get("kodepos") or row.get("kd_propins"), expected_type="string"
                )
                if kodepos:
                    kodepos = kodepos[-5:]
                gruplang = self.handle_data(row.get("gruplang"), expected_type="string")
                kodelang = self.handle_data(row.get("kodelang"), expected_type="string")
                kdcust = self.handle_data(row.get("kdcust"), expected_type="string")
                nmlang = self.handle_data(row.get("nmlang", ""), expected_type="string")
                almtlang = self.handle_data(
                    row.get("almtlang", ""), expected_type="string"
                )
                kodesalur = self.handle_data(
                    row.get("kodesalur"), expected_type="string"
                )
                nmprod = self.handle_data(row.get("nmprod", ""), expected_type="string")
                klasprod = self.handle_data(row.get("klasprod"), expected_type="string")
                principle_id = (
                    int(str(row.get("klasprod", ""))[:3][-1:])
                    if row.get("klasprod", "")
                    else None
                )
                nmklas1 = self.handle_data(
                    row.get("nmklas1", ""), expected_type="string"
                )
                nmklas2 = self.handle_data(
                    row.get("nmklas2", ""), expected_type="string"
                )
                hrdok = self.handle_data(row.get("hrdok"), expected_type="string")
                whse = self.handle_data(row.get("whse"), expected_type="string")
                whse_str = str(whse).strip() if whse else ""
                if whse_str.isdigit():
                    whse_str = f"{int(whse_str):03d}"
                nodokjdi = self.handle_data(row.get("nodokjdi"), expected_type="string")
                nodokjdi_str = str(nodokjdi).strip() if nodokjdi else ""
                if nodokjdi_str.isdigit():
                    nodokjdi_str = f"{int(nodokjdi_str):07d}"
                kodeprod = self.handle_data(row.get("kodeprod"), expected_type="string")
                banyak = self.handle_data(row.get("banyak"), expected_type="integer")
                banys = self.handle_data(row.get("banys"), expected_type="integer")
                mom = self.handle_data(row.get("mom"), expected_type="string")
                nobat = self.handle_data(row.get("nobat"), expected_type="string")
                hna = self.handle_data(row.get("hna"), expected_type="decimal")
                harga = self.handle_data(row.get("harga"), expected_type="decimal")
                thna = self.handle_data(row.get("thna"), expected_type="decimal")
                tharga = self.handle_data(row.get("tharga"), expected_type="decimal")
                pharga = self.handle_data(row.get("pharga"), expected_type="decimal")
                ehna = self.handle_data(row.get("ehna"), expected_type="decimal")
                prsnpot = self.handle_data(row.get("prsnpot"), expected_type="decimal")
                prsnbp = self.handle_data(row.get("prsnbp"), expected_type="decimal")
                prsnbmp = self.handle_data(row.get("prsnbmp"), expected_type="decimal")
                dun = self.handle_data(row.get("dun"), expected_type="string")
                idpkt = self.handle_data(row.get("idpkt"), expected_type="string")
                name = f"{hrdok}{whse_str}{nodokjdi_str}{kodeprod}"

                unique_identifier = {
                    "hrdok": hrdok,
                    "whse": whse,
                    "nodokjdi": nodokjdi_str,
                    "kodeprod": kodeprod,
                    "nobat": nobat,
                    "hna": hna,
                    "harga": harga,
                    "banyak": banyak,
                    "banys": banys,
                    "mom": mom,
                }

                # Check if customer already exists using unique identifier
                transaction = RawMUSO.objects.filter(**unique_identifier).first()
                if transaction:
                    # ✅ Customer exists → Update existing record
                    RawMUSO.objects.filter(id=transaction.id).update(
                        name=name,
                        description=description,
                        remark=remark,
                        no_order=no_order,
                        area=area,
                        kodepos=kodepos,
                        gruplang=gruplang,
                        kodelang=kodelang,
                        kdcust=kdcust,
                        nmlang=nmlang,
                        almtlang=almtlang,
                        kodesalur=kodesalur,
                        nmprod=nmprod,
                        klasprod=klasprod,
                        principle_id=principle_id,
                        nmklas1=nmklas1,
                        nmklas2=nmklas2,
                        thna=thna,
                        tharga=tharga,
                        ehna=ehna,
                        prsnpot=prsnpot,
                        pharga=pharga,
                        prsnbp=prsnbp,
                        prsnbmp=prsnbmp,
                        dun=dun,
                        idpkt=idpkt,
                        status=1,
                        uby=user_by,
                        uat=now(),
                    )
                else:
                    # ✅ New Customer → Generate Code & Create New Record
                    code = self.generate_code(
                        hrdok,
                        whse,
                        nodokjdi,
                        kodeprod,
                        nobat,
                        hna,
                        harga,
                        banyak,
                        banys,
                        mom,
                    )
                    RawMUSO.objects.create(
                        code=code,
                        name=name,
                        hrdok=hrdok,
                        whse=whse_str,
                        nodokjdi=nodokjdi_str,
                        kodeprod=kodeprod,
                        banyak=banyak,
                        banys=banys,
                        description=description,
                        remark=remark,
                        no_order=no_order,
                        area=area,
                        kodepos=kodepos,
                        gruplang=gruplang,
                        kodelang=kodelang,
                        kodcust=kdcust,
                        nmlang=nmlang,
                        almtlang=almtlang,
                        kodesalur=kodesalur,
                        nmprod=nmprod,
                        klasprod=klasprod,
                        principle_id=principle_id,
                        nmklas1=nmklas1,
                        nmklas2=nmklas2,
                        hna=hna,
                        harga=harga,
                        thna=thna,
                        tharga=tharga,
                        ehna=ehna,
                        prsnpot=prsnpot,
                        pharga=pharga,
                        prsnbp=prsnbp,
                        prsnbmp=prsnbmp,
                        mom=mom,
                        nobat=nobat,
                        dun=dun,
                        idpkt=idpkt,
                        status=1,
                        cby=user_by,
                        cat=now(),
                    )
            except Exception as e:
                error_message = (
                    f"Row {index}: Unexpected error in model admin - {str(e)}"
                )
                self.errors.append(error_message)

        # ✅ Save missing data to session for later download
        if missing_data_rows:
            request.session["missing_data"] = missing_data_rows
            messages.warning(
                request,
                mark_safe(
                    "Some rows has missing data. <a href='/base/download_missing_data/' target='_blank'>Download Missing Data</a>"
                ),
            )
            return JsonResponse(
                {"download_csv": True}
            )  # ✅ Signal frontend to download CSV

        # Show success or error messages in Django Admin
        if self.errors:
            messages.error(
                request,
                f"Import completed with {len(self.errors)} errors. Check logs for details.",
            )
            for error in self.errors:
                messages.error(request, error)
        else:
            messages.success(request, "Import completed successfully with no errors.")

        return JsonResponse({"download_csv": False})  # ✅ No CSV, just show messages


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawRNSOAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawRNSO in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/17-2025 by Noval                             ║
# ║  Updates: Jul/7-2025 by Noval                              ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawRNSO)
class RawRNSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "branch_id",
            "branch_name",
            "class_name",
            "catalog_no",
            "prod_id",
            "prod_name",
            "uom",
            "kwt",
            "price_list",
            "neto",
        )
        + (
            "disc_amt",
            "bruto",
            "invoice_date",
            "invoice_no",
            "no_pesan",
            "ref_invoice",
            "cust_id",
            "cust_id_old",
            "nama_pelanggan",
            "kategori_pelanggan",
            "kota",
            "alamat",
            "periode",
        )
        + ("code",)
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "branch_id",
            "branch_name",
            "class_name",
            "catalog_no",
            "prod_id",
            "prod_name",
            "uom",
            "kwt",
            "price_list",
            "neto",
        )
        + (
            "disc_amt",
            "bruto",
            "invoice_date",
            "invoice_no",
            "no_pesan",
            "ref_invoice",
            "cust_id",
            "cust_id_old",
            "nama_pelanggan",
            "kategori_pelanggan",
            "kota",
            "alamat",
            "periode",
        )
        + ("code",)
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "invoice_no",
                    "invoice_date",
                    "branch_id",
                    "branch_name",
                    "cust_id",
                    "cust_id_old",
                    "nama_pelanggan",
                    "kategori_pelanggan",
                    "prod_id",
                    "prod_name",
                    "kwt",
                    "uom",
                    "bruto",
                    "disc_amt",
                    "neto",
                ),
                "description": "Primary information.",
            },
        ),
        (
            "Product Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "class_name",
                    "catalog_no",
                ),
                "description": "Product information.",
            },
        ),
        (
            "Finance Info",
            {
                "classes": ("collapsed",),
                "fields": ("price_list",),
                "description": "Finance information.",
            },
        ),
        (
            "Other Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "no_pesan",
                    "ref_invoice",
                    "kota",
                    "alamat",
                    "periode",
                ),
                "description": "Other information.",
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("code", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "branch_id": "string",
        "branch_name": "string",
        "class_name": "string",
        "catalog_no": "string",
        "prod_id": "string",
        "prod_name": "string",
        "uom": "string",
        "kwt": "decimal",
        "price_list": "decimal",
        "neto": "decimal",
        "disc_amt": "decimal",
        "bruto": "decimal",
        "invoice_date": "string",
        "invoice_no": "string",
        "no_pesan": "string",
        "ref_invoice": "string",
        "cust_id": "string",
        "cust_id_old": "string",
        "nama_pelanggan": "string",
        "kategori_pelanggan": "string",
        "kota": "string",
        "alamat": "string",
        "periode": "string",
    }

    column_mapping = {  # Map external column names to internal field names
        "BRANCH_ID": "branch_id",
        "BRANCH_NAME": "branch_name",
        "CLASS_NAME": "class_name",
        "CATALOG_NO": "catalog_no",
        "PROD_ID": "prod_id",
        "PROD_NAME": "prod_name",
        "UOM": "uom",
        "KWT": "kwt",
        "PRICE_LIST": "price_list",
        "NETO": "neto",
        "DISC_AMT": "disc_amt",
        "BRUTO": "bruto",
        "INVOICE_DATE": "invoice_date",
        "INVOICE_NO": "invoice_no",
        "NO_PESAN": "no_pesan",
        "REF_INVOICE": "ref_invoice",
        "CUST_ID": "cust_id",
        "CUST_ID_OLD": "cust_id_old",
        "NAMA_PELANGGAN": "nama_pelanggan",
        "KATEGORI_PELANGGAN": "kategori_pelanggan",
        "KOTA": "kota",
        "ALAMAT": "alamat",
        "PERIODE": "periode",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
        )

    def generate_code(
        self, prod_id, invoice_date, invoice_no, kwt, cust_id, no_pesan, periode
    ):
        """
        Generate a unique customer code using custtype and an incrementing number.
        """
        invoice_no_str = str(invoice_no).replace("/", "") if invoice_no else ""
        invoice_date_str = (
            str(invoice_date).split(" ")[0].replace("-", "") if invoice_date else ""
        )
        prod_id_str = str(prod_id).strip() if prod_id else ""

        code = f"{prod_id_str}-{invoice_date_str}-{invoice_no_str}-{kwt}-{cust_id}-{no_pesan}--{periode}"  # need adjustmnet

        return code

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=dtype_mapping)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data.columns = data.columns.str.upper().str.strip()
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                #    self.message_user(request, f"Missing columns in uploaded file: {', '.join(missing_columns)}", level="error")
                #    return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]
                # Choose Upload Mode: Normal (row-by-row) or Batch Processing
                use_batch = request.POST.get(
                    "use_batch", False
                )  # ✅ Get user choice from form
                if use_batch:
                    self.message_user(
                        request, "Batch Upload Mode Enabled. Processing data..."
                    )
                    response = self.process_pandas_data_batch(
                        request, data
                    )  # ✅ Use batch processing
                else:
                    self.message_user(
                        request, "Row-by-Row Upload Mode Enabled. Processing data..."
                    )
                    response = self.process_pandas_data(
                        request, data
                    )  # ✅ Use row-by-row

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None

        # Step 1: Process Data to meet requirements
        data["invoice_date_str"] = (
            data["invoice_date"].astype(str).str.split().str[0].str.replace("-", "")
        )  # Ensure date is in string format
        data["invoice_no_str"] = (
            data["invoice_no"].astype(str).str.replace("/", "").str.strip()
        )  # Ensure invoice_no is a string without slashes

        num_as_str_fields = ["branch_id"]
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        decimal_fields = ["kwt", "price_list", "neto", "disc_amt", "bruto"]

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        string_columns = [
            "branch_id",
            "branch_name",
            "class_name",
            "catalog_no",
            "prod_id",
            "prod_name",
            "uom",
            "invoice_date",
            "invoice_no",
            "no_pesan",
            "ref_invoice",
            "cust_id",
            "cust_id_old",
            "nama_pelanggan",
            "kategori_pelanggan",
            "kota",
            "alamat",
        ]
        for col in string_columns:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["prod_id"].astype(str)
            + "-"
            + data["invoice_date"].astype(str)
            + "-"
            + data["invoice_no"].astype(str)
            + "-"
            + data["kwt"].astype(str)
            + "-"
            + data["cust_id"].astype(str)
            + "-"
            + data["no_pesan"].astype(str)
            + "-"
            + data["periode"].astype(str)
        )
        data["name"] = (
            data["prod_id"].astype(str)
            + "-"
            + data["invoice_date_str"].astype(str)
            + "-"
            + data["invoice_no_str"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )  # modify 2025-07-01

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawRNSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawRNSO(
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    name=row.get("name", ""),
                    branch_id=row.get("branch_id", ""),
                    branch_name=row.get("branch_name", ""),
                    class_name=row.get("class_name", ""),
                    catalog_no=row.get("catalog_no", ""),
                    prod_id=row.get("prod_id", ""),
                    prod_name=row.get("prod_name", ""),
                    uom=row.get("uom", ""),
                    kwt=row.get("kwt", 0.0),
                    price_list=row.get("price_list", 0.0),
                    neto=row.get("neto", 0.0),
                    disc_amt=row.get("disc_amt", 0.0),
                    bruto=row.get("bruto", 0.0),
                    invoice_date=row.get("invoice_date_str", ""),
                    invoice_no=row.get("invoice_no", ""),
                    no_pesan=row.get("no_pesan", ""),
                    ref_invoice=row.get("ref_invoice", ""),
                    cust_id=row.get("cust_id", ""),
                    cust_id_old=row.get("cust_id_old", ""),
                    nama_pelanggan=row.get("nama_pelanggan", ""),
                    kategori_pelanggan=row.get("kategori_pelanggan", ""),
                    kota=row.get("kota", ""),
                    alamat=row.get("alamat", ""),
                    periode=row.get("periode", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]
            RawRNSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawRNSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawRNSO(
                    id=existing_code_to_id.get(row["code"]),
                    branch_id=row.get("branch_id", ""),
                    branch_name=row.get("branch_name", ""),
                    class_name=row.get("class_name", ""),
                    catalog_no=row.get("catalog_no", ""),
                    prod_id=row.get("prod_id", ""),
                    prod_name=row.get("prod_name", ""),
                    uom=row.get("uom", ""),
                    kwt=row.get("kwt", 0.0),
                    price_list=row.get("price_list", 0.0),
                    neto=row.get("neto", 0.0),
                    disc_amt=row.get("disc_amt", 0.0),
                    bruto=row.get("bruto", 0.0),
                    invoice_date=row.get("invoice_date_str", ""),
                    invoice_no=row.get("invoice_no", ""),
                    no_pesan=row.get("no_pesan", ""),
                    ref_invoice=row.get("ref_invoice", ""),
                    cust_id=row.get("cust_id", ""),
                    cust_id_old=row.get("cust_id_old", ""),
                    nama_pelanggan=row.get("nama_pelanggan", ""),
                    kategori_pelanggan=row.get("kategori_pelanggan", ""),
                    kota=row.get("kota", ""),
                    alamat=row.get("alamat", ""),
                    periode=row.get("periode", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawRNSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "branch_id",
                        "branch_name",
                        "class_name",
                        "catalog_no",
                        "prod_id",
                        "prod_name",
                        "uom",
                        "kwt",
                        "price_list",
                        "neto",
                        "disc_amt",
                        "bruto",
                        "invoice_date",
                        "invoice_no",
                        "no_pesan",
                        "ref_invoice",
                        "cust_id",
                        "cust_id_old",
                        "nama_pelanggan",
                        "kategori_pelanggan",
                        "kota",
                        "alamat",
                        "periode" "description",
                        "remark",
                        "status",
                        "uby",
                        "uat",
                    ],
                )

    def process_pandas_data(self, request, data):
        """Preparation data for row-by-row processing."""
        data["invoice_date_str"] = (
            data["invoice_date"].astype(str).str.split().str[0].str.replace("-", "")
        )  # Ensure date is in string format

        """ Process the imported data and save it to the database. """
        missing_data_rows = []  # List to store rows with missing foreign keys
        total_saved = 0
        for index, row in data.iterrows():
            try:
                row_errors = []  # ✅ Store errors for this row
                # ✅ Get the logged-in user for `uby`
                user_by = request.user if request.user.is_authenticated else None
                branch_id = self.handle_data(
                    row.get("branch_id"), expected_type="string"
                )
                branch_name = self.handle_data(
                    row.get("branch_name"), expected_type="string"
                )
                class_name = self.handle_data(
                    row.get("class_name"), expected_type="string"
                )
                catalog_no = self.handle_data(
                    row.get("catalog_no"), expected_type="string"
                )
                prod_id = self.handle_data(row.get("prod_id"), expected_type="string")
                prod_name = self.handle_data(
                    row.get("prod_name"), expected_type="string"
                )
                uom = self.handle_data(row.get("uom"), expected_type="string")
                kwt = self.handle_data(row.get("kwt"), expected_type="decimal")
                price_list = self.handle_data(
                    row.get("price_list"), expected_type="decimal"
                )
                neto = self.handle_data(row.get("neto"), expected_type="decimal")
                disc_amt = self.handle_data(
                    row.get("disc_amt"), expected_type="decimal"
                )
                bruto = self.handle_data(row.get("bruto"), expected_type="decimal")
                invoice_date = self.handle_data(
                    row.get("invoice_date_str"), expected_type="string"
                )
                invoice_date_str = (
                    invoice_date.split(" ")[0].replace("-", "") if invoice_date else ""
                )
                invoice_no = self.handle_data(
                    row.get("invoice_no"), expected_type="string"
                )
                invoice_no_str = self.handle_data(
                    row.get("invoice_no"), expected_type="string"
                )
                invoice_no_str = (
                    invoice_no_str.replace("/", "") if invoice_no_str else ""
                )
                no_pesan = self.handle_data(row.get("no_pesan"), expected_type="string")
                ref_invoice = self.handle_data(
                    row.get("ref_invoice"), expected_type="string"
                )
                cust_id = self.handle_data(row.get("cust_id"), expected_type="string")
                cust_id_old = self.handle_data(
                    row.get("cust_id_old"), expected_type="string"
                )
                nama_pelanggan = self.handle_data(
                    row.get("nama_pelanggan"), expected_type="string"
                )
                kategori_pelanggan = self.handle_data(
                    row.get("kategori_pelanggan"), expected_type="string"
                )
                kota = self.handle_data(row.get("kota"), expected_type="string")
                alamat = self.handle_data(row.get("alamat"), expected_type="string")
                periode = self.handle_data(row.get("periode"), expected_type="string")
                name = f"{prod_id}-{invoice_date_str}-{invoice_no_str}"
                unique_identifier = {
                    "branch_id": branch_id,
                    "prod_id": prod_id,
                    "uom": uom,
                    "invoice_no": invoice_no,
                    "no_pesan": no_pesan,
                    "cust_id": cust_id,
                }

                # Check if customer already exists using unique identifier
                transaction = RawRNSO.objects.filter(**unique_identifier).first()
                if transaction:
                    # ✅ Customer exists → Update existing record
                    RawRNSO.objects.filter(id=transaction.id).update(
                        branch_id=branch_id,
                        branch_name=branch_name,
                        class_name=class_name,
                        catalog_no=catalog_no,
                        prod_id=prod_id,
                        prod_name=prod_name,
                        uom=uom,
                        kwt=kwt,
                        price_list=price_list,
                        neto=neto,
                        disc_amt=disc_amt,
                        bruto=bruto,
                        invoice_date=invoice_date,
                        invoice_no=invoice_no,
                        no_pesan=no_pesan,
                        ref_invoice=ref_invoice,
                        cust_id=cust_id,
                        cust_id_old=cust_id_old,
                        nama_pelanggan=nama_pelanggan,
                        kategori_pelanggan=kategori_pelanggan,
                        kota=kota,
                        alamat=alamat,
                        periode=periode,
                    )
                else:
                    # ✅ New Customer → Generate Code & Create New Record
                    code = self.generate_code(
                        prod_id,
                        invoice_date,
                        invoice_no,
                        kwt,
                        cust_id,
                        no_pesan,
                        periode,
                    )
                    RawRNSO.objects.create(
                        name=name,
                        code=code,
                        branch_id=branch_id,
                        branch_name=branch_name,
                        class_name=class_name,
                        catalog_no=catalog_no,
                        prod_id=prod_id,
                        prod_name=prod_name,
                        uom=uom,
                        kwt=kwt,
                        price_list=price_list,
                        neto=neto,
                        disc_amt=disc_amt,
                        bruto=bruto,
                        invoice_date=invoice_date,
                        invoice_no=invoice_no,
                        no_pesan=no_pesan,
                        ref_invoice=ref_invoice,
                        cust_id=cust_id,
                        cust_id_old=cust_id_old,
                        nama_pelanggan=nama_pelanggan,
                        kategori_pelanggan=kategori_pelanggan,
                        kota=kota,
                        alamat=alamat,
                        periode=periode,
                        status=1,
                        cby=user_by,
                        cat=now(),
                    )
            except Exception as e:
                error_message = (
                    f"Row {index}: Unexpected error in model admin - {str(e)}"
                )
                self.errors.append(error_message)

        # ✅ Save missing data to session for later download
        if missing_data_rows:
            request.session["missing_data"] = missing_data_rows
            messages.warning(
                request,
                mark_safe(
                    "Some rows has missing data. <a href='/base/download_missing_data/' target='_blank'>Download Missing Data</a>"
                ),
            )
            return JsonResponse(
                {"download_csv": True}
            )  # ✅ Signal frontend to download CSV

        # Show success or error messages in Django Admin
        if self.errors:
            messages.error(
                request,
                f"Import completed with {len(self.errors)} errors. Check logs for details.",
            )
            for error in self.errors:
                messages.error(request, error)
        else:
            messages.success(request, "Import completed successfully with no errors.")

        return JsonResponse({"download_csv": False})  # ✅ No CSV, just show messages


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawLMSSOAdmin                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawLMSSO in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jun/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawLMSSO)
class RawLMSSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "tanggal",
            "nomor_bukti",
            "kode_customer",
            "nama_customer",
            "alamat",
            "kota",
            "kode_cabang",
            "kode_sales",
            "nama_sales",
            "kode_barang",
            "nama_barang",
        )
        + (
            "satuan",
            "qty",
            "hna",
            "disc",
            "nilai",
            "disc_value",
            "nilai_netto",
            "total",
        )
        + ("code",)
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "tanggal",
            "nomor_bukti",
            "kode_customer",
            "nama_customer",
            "alamat",
            "kota",
            "kode_cabang",
            "kode_sales",
            "nama_sales",
            "kode_barang",
            "nama_barang",
        )
        + (
            "satuan",
            "qty",
            "hna",
            "disc",
            "nilai",
            "disc_value",
            "nilai_netto",
            "total",
            "code",
        )
    )

    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "nomor_bukti",
                    "tanggal",
                    "kode_cabang",
                    "kode_customer",
                    "nama_customer",
                    "kode_barang",
                    "nama_barang",
                    "qty",
                    "satuan",
                    "nilai",
                    "disc",
                    "disc_value",
                    "nilai_netto",
                    "total",
                ),
                "description": "Primary information.",
            },
        ),
        (
            "Product Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "class_name",
                    "catalog_no",
                ),
                "description": "Product information.",
            },
        ),
        (
            "Finance Info",
            {
                "classes": ("collapsed",),
                "fields": ("hna",),
                "description": "Finance information.",
            },
        ),
        (
            "Other Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "kode_sales",
                    "nama_sales",
                    "kota",
                    "alamat",
                ),
                "description": "Other information.",
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("code", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "tanggal": "string",
        "nomor_bukti": "string",
        "kode_customer": "string",
        "nama_customer": "string",
        "alamat": "string",
        "kota": "string",
        "kode_cabang": "string",
        "kode_sales": "string",
        "nama_sales": "string",
        "kode_barang": "string",
        "nama_barang": "string",
        "satuan": "string",
        "qty": "decimal",
        "hna": "decimal",
        "disc": "decimal",
        "nilai": "decimal",
        "disc_value": "decimal",
        "nilai_netto": "decimal",
        "total": "decimal",
    }

    column_mapping = {  # Map external column names to internal field names
        "TANGGAL": "tanggal",
        "NOMOR BUKTI": "nomor_bukti",
        "KODE CUSTOMER": "kode_customer",
        "NAMA CUSTOMER": "nama_customer",
        "ALAMAT": "alamat",
        "KOTA": "kota",
        "KODE CABANG": "kode_cabang",
        "KODE SALES": "kode_sales",
        "NAMA SALES": "nama_sales",
        "KODE BARANG": "kode_barang",
        "NAMA BARANG": "nama_barang",
        "SATUAN": "satuan",
        "QTY": "qty",
        "H.N.A": "hna",
        "DISC.": "disc",
        "NILAI": "nilai",
        "DISC. VALUE": "disc_value",
        "NILAI NETTO": "nilai_netto",
        "TOTAL": "total",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                #    self.message_user(request, f"Missing columns in uploaded file: {', '.join(missing_columns)}", level="error")
                #    return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None

        # Step 1: Process Data to meet requirements
        data["tanggal_str"] = pd.to_datetime(data["tanggal"])
        data["tanggal_str"] = data["tanggal"].dt.strftime(
            "%Y%m%d"
        )  # Ensure date is in string format
        data["nomor_bukti_str"] = (
            data["nomor_bukti"].astype(str).str.replace("-", "").str.replace(" ", "")
        )

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        decimal_fields = [
            "qty",
            "hna",
            "disc",
            "nilai",
            "disc_value",
            "nilai_netto",
            "total",
        ]

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        string_columns = [
            "tanggal",
            "nomor_bukti",
            "kode_customer",
            "nama_customer",
            "alamat",
            "kota",
            "kode_cabang",
            "kode_sales",
            "nama_sales",
            "kode_barang",
            "nama_barang",
            "satuan",
        ]
        for col in string_columns:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["tanggal_str"].astype(str)
            + "-"
            + data["nomor_bukti_str"].astype(str)
            + "-"
            + data["kode_customer"].astype(str)
            + "-"
            + data["kode_cabang"].astype(str)
            + "-"
            + data["kode_barang"].astype(str)
        )
        data["name"] = (
            data["tanggal_str"].astype(str)
            + data["kode_customer"].astype(str)
            + "-"
            + data["nomor_bukti_str"].astype(str)
            + "-"
            + data["kode_barang"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawLMSSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawLMSSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    tanggal=row.get("tanggal_str", ""),
                    nomor_bukti=row.get("nomor_bukti", ""),
                    kode_customer=row.get("kode_customer", ""),
                    nama_customer=row.get("nama_customer", ""),
                    alamat=row.get("alamat", ""),
                    kota=row.get("kota", ""),
                    kode_cabang=row.get("kode_cabang", ""),
                    kode_sales=row.get("kode_sales", ""),
                    nama_sales=row.get("nama_sales", ""),
                    kode_barang=row.get("kode_barang", ""),
                    nama_barang=row.get("nama_barang", ""),
                    satuan=row.get("satuan", ""),
                    qty=row.get("qty", 0.0),
                    hna=row.get("hna", 0.0),
                    disc=row.get("disc", 0.0),
                    nilai=row.get("nilai", 0.0),
                    disc_value=row.get("disc_value", 0.0),
                    nilai_netto=row.get("nilai_netto", 0.0),
                    total=row.get("total", 0.0),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]
            RawLMSSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawLMSSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawLMSSO(
                    id=existing_code_to_id.get(row["code"]),
                    tanggal=row.get("tanggal_str", ""),
                    nomor_bukti=row.get("nomor_bukti", ""),
                    kode_customer=row.get("kode_customer", ""),
                    nama_customer=row.get("nama_customer", ""),
                    alamat=row.get("alamat", ""),
                    kota=row.get("kota", ""),
                    kode_cabang=row.get("kode_cabang", ""),
                    kode_sales=row.get("kode_sales", ""),
                    nama_sales=row.get("nama_sales", ""),
                    kode_barang=row.get("kode_barang", ""),
                    nama_barang=row.get("nama_barang", ""),
                    satuan=row.get("satuan", ""),
                    qty=row.get("qty", 0.0),
                    hna=row.get("hna", 0.0),
                    disc=row.get("disc", 0.0),
                    nilai=row.get("nilai", 0.0),
                    disc_value=row.get("disc_value", 0.0),
                    nilai_netto=row.get("nilai_netto", 0.0),
                    total=row.get("total", 0.0),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawLMSSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "tanggal",
                        "nomor_bukti",
                        "kode_customer",
                        "nama_customer",
                        "alamat",
                        "kota",
                        "kode_cabang",
                        "kode_sales",
                        "nama_sales",
                        "kode_barang",
                        "nama_barang",
                        "satuan",
                        "qty",
                        "hna",
                        "disc",
                        "nilai",
                        "disc_value",
                        "nilai_netto",
                        "total",
                        "description",
                        "remark",
                        "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawKFSOAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawKFSO in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jun/23-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawKFSO)
class RawKFSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "sales_office",
            "desc_s_office",
            "so_type",
            "desc_sales_order",
            "billing_type",
            "posting_date",
            "billing_no",
            "posting_status",
            "bill_cancel",
            "bill_to_party",
        )
        + (
            "sold_to_party",
            "name_bill_to",
            "address",
            "city",
            "region",
            "postal_code",
            "ship_to_party",
            "name_ship_to",
            "address_ship_to",
            "city_ship_to",
        )
        + (
            "postal_code_ship_to",
            "material",
            "text_material",
            "quantity",
            "sales_unit",
            "bill_qty_in_sku",
            "uom_sku",
            "unit_price_penjualan",
            "dis_zd01",
            "dis_amt_zd01",
        )
        + (
            "dis_zd02",
            "dis_amt_zd02",
            "dis_zd03",
            "dis_amt_zd03",
            "dis_zd04",
            "dis_amt_zd04",
            "dis_zd05",
            "dis_amt_zd05",
            "dis_zd06",
            "dis_amt_zd06",
        )
        + (
            "total_discount",
            "surcharge",
            "total_penjualan",
            "tax_amount",
            "curr",
            "code_pelayanan",
            "desc_pelayanan",
            "prodh_material",
            "prod_hierarchy1",
            "prod_hierarchy2",
        )
        + (
            "prod_hierarchy3",
            "prod_hierarchy4",
            "manufactur",
            "name_manufactur",
            "principle",
            "name_principle",
            "cust_grp1",
            "desc_cust_grp1",
            "cust_grp2",
            "desc_cust_grp2",
        )
        + (
            "cust_grp3",
            "desc_cust_grp3",
            "cust_grp4",
            "desc_cust_grp4",
            "salesman",
            "name_salesman",
            "cancelled_bill_doc",
            "bill_doc_creation_date",
            "user_login_tpd_line_disc4",
        )
        + (
            "remark_ptd_4",
            "user_login_tpd_line_disc2",
            "remark_ptd_2",
            "user_login_tpd_line_disc3",
            "remark_ptd_3",
        )
        + ("code",)
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "sales_office",
            "desc_s_office",
            "so_type",
            "desc_sales_order",
            "billing_type",
            "posting_date",
            "billing_no",
            "posting_status",
            "bill_cancel",
            "bill_to_party",
        )
        + (
            "sold_to_party",
            "name_bill_to",
            "address",
            "city",
            "region",
            "postal_code",
            "ship_to_party",
            "name_ship_to",
            "address_ship_to",
            "city_ship_to",
        )
        + (
            "postal_code_ship_to",
            "material",
            "text_material",
            "quantity",
            "sales_unit",
            "bill_qty_in_sku",
            "uom_sku",
            "unit_price_penjualan",
            "dis_zd01",
            "dis_amt_zd01",
        )
        + (
            "dis_zd02",
            "dis_amt_zd02",
            "dis_zd03",
            "dis_amt_zd03",
            "dis_zd04",
            "dis_amt_zd04",
            "dis_zd05",
            "dis_amt_zd05",
            "dis_zd06",
            "dis_amt_zd06",
        )
        + (
            "total_discount",
            "surcharge",
            "total_penjualan",
            "tax_amount",
            "curr",
            "code_pelayanan",
            "desc_pelayanan",
            "prodh_material",
            "prod_hierarchy1",
            "prod_hierarchy2",
        )
        + (
            "prod_hierarchy3",
            "prod_hierarchy4",
            "manufactur",
            "name_manufactur",
            "principle",
            "name_principle",
            "cust_grp1",
            "desc_cust_grp1",
            "cust_grp2",
            "desc_cust_grp2",
        )
        + (
            "cust_grp3",
            "desc_cust_grp3",
            "cust_grp4",
            "desc_cust_grp4",
            "salesman",
            "name_salesman",
            "cancelled_bill_doc",
            "bill_doc_creation_date",
            "user_login_tpd_line_disc4",
        )
        + (
            "remark_ptd_4",
            "user_login_tpd_line_disc2",
            "remark_ptd_2",
            "user_login_tpd_line_disc3",
            "remark_ptd_3",
        )
        + ("code",)
    )

    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "sales_office",
                    "desc_s_office",
                    "so_type",
                    "desc_sales_order",
                    "billing_type",
                    "posting_date",
                    "billing_no",
                    "posting_status",
                    "bill_cancel",
                    "bill_to_party",
                )
                + (
                    "sold_to_party",
                    "name_bill_to",
                    "material",
                    "text_material",
                    "quantity",
                    "sales_unit",
                    "bill_qty_in_sku",
                    "uom_sku",
                    "total_discount",
                    "surcharge",
                    "total_penjualan",
                )
                + (
                    "tax_amount",
                    "curr",
                    "code_pelayanan",
                    "desc_pelayanan",
                    "prodh_material",
                    "prod_hierarchy1",
                    "prod_hierarchy2",
                    "prod_hierarchy3",
                    "prod_hierarchy4",
                )
                + (
                    "cust_grp1",
                    "desc_cust_grp1",
                    "cust_grp2",
                    "desc_cust_grp2",
                    "cust_grp3",
                    "desc_cust_grp3",
                    "cust_grp4",
                    "desc_cust_grp4",
                ),
                "description": "Primary information.",
            },
        ),
        (
            "Finance Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "unit_price_penjualan",
                    "dis_zd01",
                    "dis_amt_zd01",
                    "dis_zd02",
                    "dis_amt_zd02",
                    "dis_zd03",
                    "dis_amt_zd03",
                    "dis_zd04",
                    "dis_amt_zd04",
                    "dis_zd05",
                )
                + (
                    "dis_amt_zd05",
                    "dis_zd06",
                    "dis_amt_zd06",
                    "cancelled_bill_doc",
                    "bill_doc_creation_date",
                ),
                "description": "Finance information.",
            },
        ),
        (
            "Other Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "address",
                    "city",
                    "region",
                    "postal_code",
                    "ship_to_party",
                    "name_ship_to",
                    "address_ship_to",
                    "city_ship_to",
                    "postal_code_ship_to",
                )
                + (
                    "manufactur",
                    "name_manufactur",
                    "principle",
                    "name_principle",
                    "salesman",
                    "name_salesman",
                    "user_login_tpd_line_disc4",
                    "remark_ptd_4",
                )
                + (
                    "user_login_tpd_line_disc2",
                    "remark_ptd_2",
                    "user_login_tpd_line_disc3",
                    "remark_ptd_3",
                ),
                "description": "Other information.",
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("code", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "sales_office": "string",
        "desc_s_office": "string",
        "so_type": "string",
        "desc_sales_order": "string",
        "billing_type": "string",
        "posting_date": "string",
        "billing_no": "string",
        "posting_status": "string",
        "bill_cancel": "string",
        "bill_to_party": "string",
        "sold_to_party": "string",
        "name_bill_to": "string",
        "address": "string",
        "city": "string",
        "region": "string",
        "postal_code": "string",
        "ship_to_party": "string",
        "name_ship_to": "string",
        "address_ship_to": "string",
        "city_ship_to": "string",
        "postal_code_ship_to": "string",
        "material": "string",
        "text_material": "string",
        "quantity": "decimal",
        "sales_unit": "string",
        "bill_qty_in_sku": "decimal",
        "uom_sku": "string",
        "unit_price_penjualan": "decimal",
        "dis_zd01": "decimal",
        "dis_amt_zd01": "decimal",
        "dis_zd02": "decimal",
        "dis_amt_zd02": "decimal",
        "dis_zd03": "decimal",
        "dis_amt_zd03": "decimal",
        "dis_zd04": "decimal",
        "dis_amt_zd04": "decimal",
        "dis_zd05": "decimal",
        "dis_amt_zd05": "decimal",
        "dis_zd06": "decimal",
        "dis_amt_zd06": "decimal",
        "total_discount": "decimal",
        "surcharge": "decimal",
        "total_penjualan": "decimal",
        "tax_amount": "decimal",
        "curr": "string",
        "code_pelayanan": "string",
        "desc_pelayanan": "string",
        "prodh_material": "string",
        "prod_hierarchy1": "string",
        "prod_hierarchy2": "string",
        "prod_hierarchy3": "string",
        "prod_hierarchy4": "string",
        "manufactur": "string",
        "name_manufactur": "string",
        "principle": "string",
        "name_principle": "string",
        "cust_grp1": "string",
        "desc_cust_grp1": "string",
        "cust_grp2": "string",
        "desc_cust_grp2": "string",
        "cust_grp3": "string",
        "desc_cust_grp3": "string",
        "cust_grp4": "string",
        "desc_cust_grp4": "string",
        "salesman": "string",
        "name_salesman": "string",
        "cancelled_bill_doc": "string",
        "bill_doc_creation_date": "string",
        "user_login_tpd_line_disc4": "string",
        "remark_ptd_4": "string",
        "user_login_tpd_line_disc2": "string",
        "remark_ptd_2": "string",
        "user_login_tpd_line_disc3": "string",
        "remark_ptd_3": "string",
    }

    column_mapping = {  # Map external column names to internal field names
        "Sales Office": "sales_office",
        "Desc. S.Office": "desc_s_office",
        "SO Type": "so_type",
        "Desc. Sales Order": "desc_sales_order",
        "Billing Type": "billing_type",
        "Posting Date": "posting_date",
        "Billing No": "billing_no",
        "Posting Status": "posting_status",
        "Bill.Cancel": "bill_cancel",
        "Bill To party": "bill_to_party",
        "Sold To party": "sold_to_party",
        "Name Bill To": "name_bill_to",
        "Address": "address",
        "City": "city",
        "Region": "region",
        "Postal Code": "postal_code",
        "Ship To party": "ship_to_party",
        "Name Ship To": "name_ship_to",
        "Address Ship To": "address_ship_to",
        "City Ship To": "city_ship_to",
        "Postal Code Ship To": "postal_code_ship_to",
        "Material": "material",
        "Text Material": "text_material",
        "Quantity": "quantity",
        "Sales Unit": "sales_unit",
        "Bill Qty in SKU": "bill_qty_in_sku",
        "UoM SKU": "uom_sku",
        "Unit Price Penjualan": "unit_price_penjualan",
        "Dis% (ZD01)": "dis_zd01",
        "DisAmt (ZD01)": "dis_amt_zd01",
        "Dis% (ZD02)": "dis_zd02",
        "DisAmt (ZD02)": "dis_amt_zd02",
        "Dis% (ZD03)": "dis_zd03",
        "DisAmt (ZD03)": "dis_amt_zd03",
        "Dis% (ZD04)": "dis_zd04",
        "DisAmt (ZD04)": "dis_amt_zd04",
        "Dis% (ZD05)": "dis_zd05",
        "DisAmt (ZD05)": "dis_amt_zd05",
        "Dis% (ZD06)": "dis_zd06",
        "DisAmt (ZD06)": "dis_amt_zd06",
        "Total Discount": "total_discount",
        "Surcharge": "surcharge",
        "Total Penjualan": "total_penjualan",
        "Tax Amount": "tax_amount",
        "CURR": "curr",
        "Code Pelayanan": "code_pelayanan",
        "Des. Pelayanan": "desc_pelayanan",
        "Prodh. Material": "prodh_material",
        "Prod. Hierarchy 1": "prod_hierarchy1",
        "Prod. Hierarchy 2": "prod_hierarchy2",
        "Prod. Hierarchy 3": "prod_hierarchy3",
        "Prod. Hierarchy 4": "prod_hierarchy4",
        "Manufactur": "manufactur",
        "Name Manufactur": "name_manufactur",
        "Principle": "principle",
        "Name Principle": "name_principle",
        "Cust. Grp1": "cust_grp1",
        "Desc. Cust. Grp1": "desc_cust_grp1",
        "Cust. Grp2": "cust_grp2",
        "Desc. Cust. Grp2": "desc_cust_grp2",
        "Cust. Grp3": "cust_grp3",
        "Desc. Cust. Grp3": "desc_cust_grp3",
        "Cust. Grp4": "cust_grp4",
        "Desc. Cust. Grp4": "desc_cust_grp4",
        "Salesman": "salesman",
        "Name Salesman": "name_salesman",
        "Cancelled Bill.Doc.": "cancelled_bill_doc",
        "Bill.Doc.Creation Date": "bill_doc_creation_date",
        "User Login TPD (Line Disc4)": "user_login_tpd_line_disc4",
        "Remark PTD 4": "remark_ptd_4",
        "User Login TPD (Line Disc2)": "user_login_tpd_line_disc2",
        "Remark PTD 2": "remark_ptd_2",
        "User Login TPD (Line Disc3)": "user_login_tpd_line_disc3",
        "Remark PTD 3": "remark_ptd_3",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                #    self.message_user(request, f"Missing columns in uploaded file: {', '.join(missing_columns)}", level="error")
                #    return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements
        data["posting_date"] = pd.to_datetime(data["posting_date"])
        data["posting_date"] = data["posting_date"].dt.strftime(
            "%Y%m%d"
        )  # Ensure date is in string format
        data["bill_doc_creation_date"] = pd.to_datetime(data["bill_doc_creation_date"])
        data["bill_doc_creation_date"] = data["bill_doc_creation_date"].dt.strftime(
            "%Y%m%d"
        )  # Ensure date is in string format

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["posting_date"].astype(str)
            + "-"
            + data["billing_no"].astype(str)
            + "-"
            + data["sales_office"].astype(str)
            + "-"
            + data["material"].astype(str)
            + "-"
            + data["quantity"].astype(str)
            + "-"
            + data["so_type"].astype(str)
            + "-"
            + data["sold_to_party"].astype(str)
            + "-"
            + data["remark_ptd_2"].astype(str)
            + "-"
            + data["quantity"].astype(str)
        )

        data["name"] = (
            data["posting_date"].astype(str)
            + data["sales_office"].astype(str)
            + "-"
            + data["billing_no"].astype(str)
            + "-"
            + data["material"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawKFSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawKFSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    sales_office=row.get("sales_office", ""),
                    desc_s_office=row.get("desc_s_office", ""),
                    so_type=row.get("so_type", ""),
                    desc_sales_order=row.get("desc_sales_order", ""),
                    billing_type=row.get("billing_type", ""),
                    posting_date=row.get("posting_date", ""),
                    billing_no=row.get("billing_no", ""),
                    posting_status=row.get("posting_status", ""),
                    bill_cancel=row.get("bill_cancel", ""),
                    bill_to_party=row.get("bill_to_party", ""),
                    sold_to_party=row.get("sold_to_party", ""),
                    name_bill_to=row.get("name_bill_to", ""),
                    address=row.get("address", ""),
                    city=row.get("city", ""),
                    region=row.get("region", ""),
                    postal_code=row.get("postal_code", ""),
                    ship_to_party=row.get("ship_to_party", ""),
                    name_ship_to=row.get("name_ship_to", ""),
                    address_ship_to=row.get("address_ship_to", ""),
                    city_ship_to=row.get("city_ship_to", ""),
                    postal_code_ship_to=row.get("postal_code_ship_to", ""),
                    material=row.get("material", ""),
                    text_material=row.get("text_material", ""),
                    quantity=row.get("quantity", 0.0),
                    sales_unit=row.get("sales_unit", ""),
                    bill_qty_in_sku=row.get("bill_qty_in_sku", 0.0),
                    uom_sku=row.get("uom_sku", ""),
                    unit_price_penjualan=row.get("unit_price_penjualan", 0.0),
                    dis_zd01=row.get("dis_zd01", 0.0),
                    dis_amt_zd01=row.get("dis_amt_zd01", 0.0),
                    dis_zd02=row.get("dis_zd02", 0.0),
                    dis_amt_zd02=row.get("dis_amt_zd02", 0.0),
                    dis_zd03=row.get("dis_zd03", 0.0),
                    dis_amt_zd03=row.get("dis_amt_zd03", 0.0),
                    dis_zd04=row.get("dis_zd04", 0.0),
                    dis_amt_zd04=row.get("dis_amt_zd04", 0.0),
                    dis_zd05=row.get("dis_zd05", 0.0),
                    dis_amt_zd05=row.get("dis_amt_zd05", 0.0),
                    dis_zd06=row.get("dis_zd06", 0.0),
                    dis_amt_zd06=row.get("dis_amt_zd06", 0.0),
                    total_discount=row.get("total_discount", 0.0),
                    surcharge=row.get("surcharge", 0.0),
                    total_penjualan=row.get("total_penjualan", 0.0),
                    tax_amount=row.get("tax_amount", 0.0),
                    curr=row.get("curr", ""),
                    code_pelayanan=row.get("code_pelayanan", ""),
                    desc_pelayanan=row.get("desc_pelayanan", ""),
                    prodh_material=row.get("prodh_material", ""),
                    prod_hierarchy1=row.get("prod_hierarchy1", ""),
                    prod_hierarchy2=row.get("prod_hierarchy2", ""),
                    prod_hierarchy3=row.get("prod_hierarchy3", ""),
                    prod_hierarchy4=row.get("prod_hierarchy4", ""),
                    manufactur=row.get("manufactur", ""),
                    name_manufactur=row.get("name_manufactur", ""),
                    principle=row.get("principle", ""),
                    name_principle=row.get("name_principle", ""),
                    cust_grp1=row.get("cust_grp1", ""),
                    desc_cust_grp1=row.get("desc_cust_grp1", ""),
                    cust_grp2=row.get("cust_grp2", ""),
                    desc_cust_grp2=row.get("desc_cust_grp2", ""),
                    cust_grp3=row.get("cust_grp3", ""),
                    desc_cust_grp3=row.get("desc_cust_grp3", ""),
                    cust_grp4=row.get("cust_grp4", ""),
                    desc_cust_grp4=row.get("desc_cust_grp4", ""),
                    salesman=row.get("salesman", ""),
                    name_salesman=row.get("name_salesman", ""),
                    cancelled_bill_doc=row.get("cancelled_bill_doc", ""),
                    bill_doc_creation_date=row.get("bill_doc_creation_date", ""),
                    user_login_tpd_line_disc4=row.get("user_login_tpd_line_disc4", ""),
                    remark_ptd_4=row.get("remark_ptd_4", ""),
                    user_login_tpd_line_disc2=row.get("user_login_tpd_line_disc2", ""),
                    remark_ptd_2=row.get("remark_ptd_2", ""),
                    user_login_tpd_line_disc3=row.get("user_login_tpd_line_disc3", ""),
                    remark_ptd_3=row.get("remark_ptd_3", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            RawKFSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawKFSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawKFSO(
                    id=existing_code_to_id.get(row["code"]),
                    sales_office=row.get("sales_office", ""),
                    desc_s_office=row.get("desc_s_office", ""),
                    so_type=row.get("so_type", ""),
                    desc_sales_order=row.get("desc_sales_order", ""),
                    billing_type=row.get("billing_type", ""),
                    posting_date=row.get("posting_date", ""),
                    billing_no=row.get("billing_no", ""),
                    posting_status=row.get("posting_status", ""),
                    bill_cancel=row.get("bill_cancel", ""),
                    bill_to_party=row.get("bill_to_party", ""),
                    sold_to_party=row.get("sold_to_party", ""),
                    name_bill_to=row.get("name_bill_to", ""),
                    address=row.get("address", ""),
                    city=row.get("city", ""),
                    region=row.get("region", ""),
                    postal_code=row.get("postal_code", ""),
                    ship_to_party=row.get("ship_to_party", ""),
                    name_ship_to=row.get("name_ship_to", ""),
                    address_ship_to=row.get("address_ship_to", ""),
                    city_ship_to=row.get("city_ship_to", ""),
                    postal_code_ship_to=row.get("postal_code_ship_to", ""),
                    material=row.get("material", ""),
                    text_material=row.get("text_material", ""),
                    quantity=row.get("quantity", 0.0),
                    sales_unit=row.get("sales_unit", ""),
                    bill_qty_in_sku=row.get("bill_qty_in_sku", 0.0),
                    uom_sku=row.get("uom_sku", ""),
                    unit_price_penjualan=row.get("unit_price_penjualan", 0.0),
                    dis_zd01=row.get("dis_zd01", 0.0),
                    dis_amt_zd01=row.get("dis_amt_zd01", 0.0),
                    dis_zd02=row.get("dis_zd02", 0.0),
                    dis_amt_zd02=row.get("dis_amt_zd02", 0.0),
                    dis_zd03=row.get("dis_zd03", 0.0),
                    dis_amt_zd03=row.get("dis_amt_zd03", 0.0),
                    dis_zd04=row.get("dis_zd04", 0.0),
                    dis_amt_zd04=row.get("dis_amt_zd04", 0.0),
                    dis_zd05=row.get("dis_zd05", 0.0),
                    dis_amt_zd05=row.get("dis_amt_zd05", 0.0),
                    dis_zd06=row.get("dis_zd06", 0.0),
                    dis_amt_zd06=row.get("dis_amt_zd06", 0.0),
                    total_discount=row.get("total_discount", 0.0),
                    surcharge=row.get("surcharge", 0.0),
                    total_penjualan=row.get("total_penjualan", 0.0),
                    tax_amount=row.get("tax_amount", 0.0),
                    curr=row.get("curr", ""),
                    code_pelayanan=row.get("code_pelayanan", ""),
                    desc_pelayanan=row.get("desc_pelayanan", ""),
                    prodh_material=row.get("prodh_material", ""),
                    prod_hierarchy1=row.get("prod_hierarchy1", ""),
                    prod_hierarchy2=row.get("prod_hierarchy2", ""),
                    prod_hierarchy3=row.get("prod_hierarchy3", ""),
                    prod_hierarchy4=row.get("prod_hierarchy4", ""),
                    manufactur=row.get("manufactur", ""),
                    name_manufactur=row.get("name_manufactur", ""),
                    principle=row.get("principle", ""),
                    name_principle=row.get("name_principle", ""),
                    cust_grp1=row.get("cust_grp1", ""),
                    desc_cust_grp1=row.get("desc_cust_grp1", ""),
                    cust_grp2=row.get("cust_grp2", ""),
                    desc_cust_grp2=row.get("desc_cust_grp2", ""),
                    cust_grp3=row.get("cust_grp3", ""),
                    desc_cust_grp3=row.get("desc_cust_grp3", ""),
                    cust_grp4=row.get("cust_grp4", ""),
                    desc_cust_grp4=row.get("desc_cust_grp4", ""),
                    salesman=row.get("salesman", ""),
                    name_salesman=row.get("name_salesman", ""),
                    cancelled_bill_doc=row.get("cancelled_bill_doc", ""),
                    bill_doc_creation_date=row.get("bill_doc_creation_date", ""),
                    user_login_tpd_line_disc4=row.get("user_login_tpd_line_disc4", ""),
                    remark_ptd_4=row.get("remark_ptd_4", ""),
                    user_login_tpd_line_disc2=row.get("user_login_tpd_line_disc2", ""),
                    remark_ptd_2=row.get("remark_ptd_2", ""),
                    user_login_tpd_line_disc3=row.get("user_login_tpd_line_disc3", ""),
                    remark_ptd_3=row.get("remark_ptd_3", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawKFSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "sales_office",
                        "desc_s_office",
                        "so_type",
                        "desc_sales_order",
                        "billing_type",
                        "posting_date",
                        "billing_no",
                        "posting_status",
                        "bill_cancel",
                        "bill_to_party",
                        "sold_to_party",
                        "name_bill_to",
                        "address",
                        "city",
                        "region",
                        "postal_code",
                        "ship_to_party",
                        "name_ship_to",
                        "address_ship_to",
                        "city_ship_to",
                        "postal_code_ship_to",
                        "material",
                        "text_material",
                        "quantity",
                        "sales_unit",
                        "bill_qty_in_sku",
                        "uom_sku",
                        "unit_price_penjualan",
                        "dis_zd01",
                        "dis_amt_zd01",
                        "dis_zd02",
                        "dis_amt_zd02",
                        "dis_zd03",
                        "dis_amt_zd03",
                        "dis_zd04",
                        "dis_amt_zd04",
                        "dis_zd05",
                        "dis_amt_zd05",
                        "dis_zd06",
                        "dis_amt_zd06",
                        "total_discount",
                        "surcharge",
                        "total_penjualan",
                        "tax_amount",
                        "curr",
                        "code_pelayanan",
                        "desc_pelayanan",
                        "prodh_material",
                        "prod_hierarchy1",
                        "prod_hierarchy2",
                        "prod_hierarchy3",
                        "prod_hierarchy4",
                        "manufactur",
                        "name_manufactur",
                        "principle",
                        "name_principle",
                        "cust_grp1",
                        "desc_cust_grp1",
                        "cust_grp2",
                        "desc_cust_grp2",
                        "cust_grp3",
                        "desc_cust_grp3",
                        "cust_grp4",
                        "desc_cust_grp4",
                        "salesman",
                        "name_salesman",
                        "cancelled_bill_doc",
                        "bill_doc_creation_date",
                        "user_login_tpd_line_disc4",
                        "remark_ptd_4",
                        "user_login_tpd_line_disc2",
                        "remark_ptd_2",
                        "user_login_tpd_line_disc3",
                        "remark_ptd_3",
                        "description",
                        "remark",
                        "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawIGSOAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawIGSO in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jun/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawIGSO)
class RawIGSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "tanggal_trans",
            "cabang",
            "kode_cust",
            "cust_desc",
            "cust_city",
            "cust_addr",
            "cust_group",
            "invoice_number",
            "type_sales",
        )
        + (
            "item",
            "item_desc",
            "principal",
            "qty",
            "hpp",
            "disc_igm",
            "percent_igm",
            "disc_princip",
            "percent_princip",
            "disc_marketing",
        )
        + (
            "percent_marketing",
            "gross",
            "sales_nett",
            "do_number",
            "id_paket",
            "invoice_referensi",
            "salesman",
            "group_produk",
            "group_principal",
            "tax_amount",
        )
        + (
            "tax_code",
            "seri_pajak",
            "pengantar_barang",
            "cash_disc",
            "cash_percent",
            "tgl_do_posting",
            "remarks_so",
            "no_kontrak",
            "no_epdo",
            "referensi_epdo",
        )
        + (
            "kurs",
            "currency",
            "top",
            "mr_inaf",
            "outsourcing_salesman",
            "so_number",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "code",
            "tanggal_trans",
            "cabang",
            "kode_cust",
            "cust_desc",
            "cust_city",
            "cust_addr",
            "cust_group",
            "invoice_number",
            "type_sales",
        )
        + (
            "item",
            "item_desc",
            "principal",
            "qty",
            "hpp",
            "disc_igm",
            "percent_igm",
            "disc_princip",
            "percent_princip",
            "disc_marketing",
        )
        + (
            "percent_marketing",
            "gross",
            "sales_nett",
            "do_number",
            "id_paket",
            "invoice_referensi",
            "salesman",
            "group_produk",
            "group_principal",
            "tax_amount",
        )
        + (
            "tax_code",
            "seri_pajak",
            "pengantar_barang",
            "cash_disc",
            "cash_percent",
            "tgl_do_posting",
            "remarks_so",
            "no_kontrak",
            "no_epdo",
            "referensi_epdo",
        )
        + (
            "kurs",
            "currency",
            "top",
            "mr_inaf",
            "outsourcing_salesman",
            "so_number",
        )
    )

    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "tanggal_trans",
                    "invoice_number",
                    "cabang",
                    "kode_cust",
                    "cust_desc",
                    "cust_group",
                    "type_sales",
                    "item",
                    "item_desc",
                )
                + (
                    "qty",
                    "gross",
                    "sales_nett",
                ),
                "description": "Primary information.",
            },
        ),
        (
            "Finance Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "hpp",
                    "disc_igm",
                    "percent_igm",
                    "disc_princip",
                    "percent_princip",
                    "disc_marketing",
                    "percent_marketing",
                    "tax_amount",
                )
                + (
                    "tax_code",
                    "seri_pajak",
                    "invoice_referensi",
                    "cash_disc",
                    "cash_percent",
                    "kurs",
                    "currency",
                    "top",
                ),
                "description": "Finance information.",
            },
        ),
        (
            "Other Info",
            {
                "classes": ("collapsed",),
                "fields": (
                    "cust_addr",
                    "cust_city",
                    "principal",
                    "do_number",
                    "id_paket",
                    "salesman",
                    "group_produk",
                    "group_principal",
                    "pengantar_barang",
                )
                + (
                    "tgl_do_posting",
                    "remarks_so",
                    "no_kontrak",
                    "no_epdo",
                    "referensi_epdo",
                    "mr_inaf",
                    "outsourcing_salesman",
                    "so_number",
                ),
                "description": "Other information.",
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("code", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )

    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "tanggal_trans": "string",
        "cabang": "string",
        "kode_cust": "string",
        "cust_desc": "string",
        "cust_city": "string",
        "cust_addr": "string",
        "cust_group": "string",
        "invoice_number": "string",
        "type_sales": "string",
        "item": "string",
        "item_desc": "string",
        "principal": "string",
        "qty": "decimal",
        "hpp": "decimal",
        "disc_igm": "decimal",
        "percent_igm": "decimal",
        "disc_princip": "decimal",
        "percent_princip": "decimal",
        "disc_marketing": "decimal",
        "percent_marketing": "decimal",
        "gross": "decimal",
        "sales_nett": "decimal",
        "do_number": "string",
        "id_paket": "string",
        "invoice_referensi": "string",
        "salesman": "string",
        "group_produk": "string",
        "group_principal": "string",
        "tax_amount": "decimal",
        "tax_code": "string",
        "seri_pajak": "string",
        "pengantar_barang": "string",
        "cash_disc": "decimal",
        "cash_percent": "decimal",
        "tgl_do_posting": "string",
        "remarks_so": "string",
        "no_kontrak": "string",
        "no_epdo": "string",
        "referensi_epdo": "string",
        "kurs": "decimal",
        "currency": "string",
        "top": "string",
        "mr_inaf": "string",
        "outsourcing_salesman": "string",
        "so_number": "string",
    }

    column_mapping = {
        "Code": "code",
        "Tanggal Trans": "tanggal_trans",
        "Cabang": "cabang",
        "Kode Cust": "kode_cust",
        "Cust Desc": "cust_desc",
        "Cust City": "cust_city",
        "Cust Addr": "cust_addr",
        "Cust Group": "cust_group",
        "Invoice Number": "invoice_number",
        "Type Sales": "type_sales",
        "Item": "item",
        "Item Desc": "item_desc",
        "Principal": "principal",
        "QTY": "qty",
        "HPP": "hpp",
        "Disc IGM": "disc_igm",
        "Percent IGM": "percent_igm",
        "Disc PRINC": "disc_princip",
        "Percent PRINC": "percent_princip",
        "Disc Marketing": "disc_marketing",
        "Percent Marketing": "percent_marketing",
        "Gross": "gross",
        "Sales Nett": "sales_nett",
        "DO Number": "do_number",
        "ID Paket": "id_paket",
        "Invoice Referensi": "invoice_referensi",
        "Salesman": "salesman",
        "Group Produk": "group_produk",
        "Group Principal": "group_principal",
        "Tax Amount": "tax_amount",
        "Tax Code": "tax_code",
        "Seri Pajak": "seri_pajak",
        "Pengantar Barang": "pengantar_barang",
        "Cash Disc": "cash_disc",
        "Cash Percent": "cash_percent",
        "Tgl DO Posting": "tgl_do_posting",
        "Remarks SO": "remarks_so",
        "No Kontrak": "no_kontrak",
        "No EPDO": "no_epdo",
        "Referensi EPDO": "referensi_epdo",
        "Kurs": "kurs",
        "Currency": "currency",
        "TOP": "top",
        "MR INAF": "mr_inaf",
        "Outsourcing Salesman": "outsourcing_salesman",
        "SO Number": "so_number",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                #    self.message_user(request, f"Missing columns in uploaded file: {', '.join(missing_columns)}", level="error")
                #    return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def clean_tax_amount(self, value):
        try:
            parts = str(value).split(".")
            if parts[-1] == "00" or parts[-1] == "00-":
                return float("".join(parts[:-1]))
            return float(value)
        except Exception:
            return value

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements
        data["tanggal_trans"] = pd.to_datetime(data["tanggal_trans"])
        data["tanggal_trans"] = data["tanggal_trans"].dt.strftime(
            "%Y%m%d"
        )  # Ensure date is in string format
        data["tgl_do_posting"] = pd.to_datetime(data["tgl_do_posting"])
        data["tgl_do_posting"] = data["tgl_do_posting"].dt.strftime(
            "%Y%m%d"
        )  # Ensure date is in string format
        data["tax_amount"] = data["tax_amount"].apply(self.clean_tax_amount)

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["tanggal_trans"].astype(str)
            + "-"
            + data["kode_cust"].astype(str)
            + "-"
            + data["invoice_number"].astype(str)
            + "-"
            + data["item"].astype(str)
            + "-"
            + data["qty"].astype(str)
            + "-"
            + data["hpp"].astype(str)
            + "-"
            + data["tgl_do_posting"].astype(str)
        )

        data["name"] = (
            data["tanggal_trans"].astype(str)
            + data["kode_cust"].astype(str)
            + "-"
            + data["invoice_number"].astype(str)
            + "-"
            + data["item"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawIGSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawIGSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    tanggal_trans=row.get("tanggal_trans", ""),
                    cabang=row.get("cabang", ""),
                    kode_cust=row.get("kode_cust", ""),
                    cust_desc=row.get("cust_desc", ""),
                    cust_city=row.get("cust_city", ""),
                    cust_addr=row.get("cust_addr", ""),
                    cust_group=row.get("cust_group", ""),
                    invoice_number=row.get("invoice_number", ""),
                    type_sales=row.get("type_sales", ""),
                    item=row.get("item", ""),
                    item_desc=row.get("item_desc", ""),
                    principal=row.get("principal", ""),
                    qty=row.get("qty", 0.0),
                    hpp=row.get("hpp", 0.0),
                    disc_igm=row.get("disc_igm", 0.0),
                    percent_igm=row.get("percent_igm", 0.0),
                    disc_princip=row.get("disc_princip", 0.0),
                    percent_princip=row.get("percent_princip", 0.0),
                    disc_marketing=row.get("disc_marketing", 0.0),
                    percent_marketing=row.get("percent_marketing", 0.0),
                    gross=row.get("gross", 0.0),
                    sales_nett=row.get("sales_nett", 0.0),
                    do_number=row.get("do_number", ""),
                    id_paket=row.get("id_paket", ""),
                    invoice_referensi=row.get("invoice_referensi", ""),
                    salesman=row.get("salesman", ""),
                    group_produk=row.get("group_produk", ""),
                    group_principal=row.get("group_principal", ""),
                    tax_amount=row.get("tax_amount", 0.0),
                    tax_code=row.get("tax_code", ""),
                    seri_pajak=row.get("seri_pajak", ""),
                    pengantar_barang=row.get("pengantar_barang", ""),
                    cash_disc=row.get("cash_disc", 0.0),
                    cash_percent=row.get("cash_percent", 0.0),
                    tgl_do_posting=row.get("tgl_do_posting", ""),
                    remarks_so=row.get("remarks_so", ""),
                    no_kontrak=row.get("no_kontrak", ""),
                    no_epdo=row.get("no_epdo", ""),
                    referensi_epdo=row.get("referensi_epdo", ""),
                    kurs=row.get("kurs", 0.0),
                    currency=row.get("currency", ""),
                    top=row.get("top", ""),
                    mr_inaf=row.get("mr_inaf", ""),
                    outsourcing_salesman=row.get("outsourcing_salesman", ""),
                    so_number=row.get("so_number", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            RawIGSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawIGSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawIGSO(
                    id=existing_code_to_id.get(row["code"]),
                    tanggal_trans=row.get("tanggal_trans", ""),
                    cabang=row.get("cabang", ""),
                    kode_cust=row.get("kode_cust", ""),
                    cust_desc=row.get("cust_desc", ""),
                    cust_city=row.get("cust_city", ""),
                    cust_addr=row.get("cust_addr", ""),
                    cust_group=row.get("cust_group", ""),
                    invoice_number=row.get("invoice_number", ""),
                    type_sales=row.get("type_sales", ""),
                    item=row.get("item", ""),
                    item_desc=row.get("item_desc", ""),
                    principal=row.get("principal", ""),
                    qty=row.get("qty", 0.0),
                    hpp=row.get("hpp", 0.0),
                    disc_igm=row.get("disc_igm", 0.0),
                    percent_igm=row.get("percent_igm", 0.0),
                    disc_princip=row.get("disc_princip", 0.0),
                    percent_princip=row.get("percent_princip", 0.0),
                    disc_marketing=row.get("disc_marketing", 0.0),
                    percent_marketing=row.get("percent_marketing", 0.0),
                    gross=row.get("gross", 0.0),
                    sales_nett=row.get("sales_nett", 0.0),
                    do_number=row.get("do_number", ""),
                    id_paket=row.get("id_paket", ""),
                    invoice_referensi=row.get("invoice_referensi", ""),
                    salesman=row.get("salesman", ""),
                    group_produk=row.get("group_produk", ""),
                    group_principal=row.get("group_principal", ""),
                    tax_amount=row.get("tax_amount", 0.0),
                    tax_code=row.get("tax_code", ""),
                    seri_pajak=row.get("seri_pajak", ""),
                    pengantar_barang=row.get("pengantar_barang", ""),
                    cash_disc=row.get("cash_disc", 0.0),
                    cash_percent=row.get("cash_percent", 0.0),
                    tgl_do_posting=row.get("tgl_do_posting", ""),
                    remarks_so=row.get("remarks_so", ""),
                    no_kontrak=row.get("no_kontrak", ""),
                    no_epdo=row.get("no_epdo", ""),
                    referensi_epdo=row.get("referensi_epdo", ""),
                    kurs=row.get("kurs", 0.0),
                    currency=row.get("currency", ""),
                    top=row.get("top", ""),
                    mr_inaf=row.get("mr_inaf", ""),
                    outsourcing_salesman=row.get("outsourcing_salesman", ""),
                    so_number=row.get("so_number", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawIGSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "tanggal_trans",
                        "cabang",
                        "kode_cust",
                        "cust_desc",
                        "cust_city",
                        "cust_addr",
                        "cust_group",
                        "invoice_number",
                        "type_sales",
                        "item",
                        "item_desc",
                        "principal",
                        "qty",
                        "hpp",
                        "disc_igm",
                        "percent_igm",
                        "disc_princip",
                        "percent_princip",
                        "disc_marketing",
                        "percent_marketing",
                        "gross",
                        "sales_nett",
                        "do_number",
                        "id_paket",
                        "invoice_referensi",
                        "salesman",
                        "group_produk",
                        "group_principal",
                        "tax_amount",
                        "tax_code",
                        "seri_pajak",
                        "pengantar_barang",
                        "cash_disc",
                        "cash_percent",
                        "tgl_do_posting",
                        "remarks_so",
                        "no_kontrak",
                        "no_epdo",
                        "referensi_epdo",
                        "kurs",
                        "currency",
                        "top",
                        "mr_inaf",
                        "outsourcing_salesman",
                        "so_number",
                        "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawPPSOAdmin                                        ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawPPSO in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/19-2025 by Noval                             ║
# ║  Updates: Jun/26-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawPPSO)
class RawPPSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "cabang",
            "nama_outlet",
            "kode_outlet",
            "kode_produk",
            "nama_produk",
            "qty_botol",
            "value_rp",
            "tanggal_invoice",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "cabang",
        "nama_outlet",
        "kode_outlet",
        "kode_produk",
        "nama_produk",
        "qty_botol",
        "value_rp",
        "tanggal_invoice",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "cabang": "string",
        "nama_outlet": "string",
        "kode_outlet": "string",
        "kode_produk": "string",
        "nama_produk": "string",
        "qty_botol": "decimal",
        "value_rp": "decimal",
        "tanggal_invoice": "string",
    }

    column_mapping = {
        "Code": "code",
        "Cabang": "cabang",
        "Nama Outlet": "nama_outlet",
        "Kode Outlet": "kode_outlet",
        "Kode Produk": "kode_produk",
        "Nama Produk": "nama_produk",
        "Qty Botol": "qty_botol",
        "Value Rp": "value_rp",
        "Tanggal Invoice": "tanggal_invoice",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements

        data["tanggal_invoice"] = pd.to_datetime(data["tanggal_invoice"])
        data["tanggal_invoice"] = data["tanggal_invoice"].dt.strftime(
            "%Y%m%d"
        )  # Ensure date is in string format

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["tanggal_invoice"].astype(str)
            + data["cabang"].astype(str)
            + "-"
            + data["kode_produk"].astype(str)
            + "-"
            + data["qty_botol"].astype(str)
        )

        data["name"] = (
            data["tanggal_invoice"].astype(str)
            + data["cabang"].astype(str)
            + "-"
            + data["kode_produk"].astype(str)
            + "-"
            + data["qty_botol"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawPPSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawPPSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    cabang=row.get("cabang", ""),
                    nama_outlet=row.get("nama_outlet", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    kode_produk=row.get("kode_produk", ""),
                    nama_produk=row.get("nama_produk", ""),
                    qty_botol=row.get("qty_botol", 0.0),
                    value_rp=row.get("value_rp", 0.0),
                    tanggal_invoice=row.get("tanggal_invoice", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            RawPPSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawPPSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawPPSO(
                    id=existing_code_to_id.get(row["code"]),
                    cabang=row.get("cabang", ""),
                    nama_outlet=row.get("nama_outlet", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    kode_produk=row.get("kode_produk", ""),
                    nama_produk=row.get("nama_produk", ""),
                    qty_botol=row.get("qty_botol", 0.0),
                    value_rp=row.get("value_rp", 0.0),
                    tanggal_invoice=row.get("tanggal_invoice", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawPPSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "cabang",
                        "nama_outlet",
                        "kode_outlet",
                        "kode_produk",
                        "nama_produk",
                        "qty_botol",
                        "value_rp",
                        "tanggal_invoice",
                        "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawAPLSOAdmin                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawAPLSO in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/30-2025 by Noval                             ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawAPLSO)
class RawAPLSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "kode_distributor",
            "type",
            "facno",
            "tanggal",
            "kode_produk",
            "produk",
            "kode_produk_oi",
            "produk_oi",
            "kode_group_produk",
            "group_produk",
            "kode_subgroup_produk",
            "subgroup_produk",
            "kode_branch",
            "branch",
            "id_branch_oi",
            "kode_branch_oi",
            "branch_oi",
            "kode_outlet",
            "cust_id",
            "outlet",
            "alamat_outlet",
            "kode_outlet_oi",
            "outlet_oi",
            "alamat_outlet_oi",
            "kode_group_outlet",
            "group_outlet",
            "kode_salur",
            "kode_sector",
            "sector",
            "kode_channel",
            "channel",
            "kode_sub_channel",
            "sub_channel",
            "kode_region",
            "region",
            "qty",
            "faktor_kali",
            "hjp",
            "hna",
            "harga",
            "whse",
            "tanggal_expired",
            "batch",
            "prsnd",
            "prsnpot",
            "prsnt",
            "prsnbp",
            "prsnbmp",
            "bonus",
            "facAcu",
            "kode_team",
            "team",
            "dun",
            "distribute_apks",
            "distributed_id",
            "distributed_name",
            "parent_id",
            "missing_facno",
            "no_order",
            "periode",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "kode_distributor",
        "type",
        "facno",
        "tanggal",
        "kode_produk",
        "produk",
        "kode_produk_oi",
        "produk_oi",
        "kode_group_produk",
        "group_produk",
        "kode_subgroup_produk",
        "subgroup_produk",
        "kode_branch",
        "branch",
        "id_branch_oi",
        "kode_branch_oi",
        "branch_oi",
        "kode_outlet",
        "cust_id",
        "outlet",
        "alamat_outlet",
        "kode_outlet_oi",
        "outlet_oi",
        "alamat_outlet_oi",
        "kode_group_outlet",
        "group_outlet",
        "kode_salur",
        "kode_sector",
        "sector",
        "kode_channel",
        "channel",
        "kode_sub_channel",
        "sub_channel",
        "kode_region",
        "region",
        "qty",
        "faktor_kali",
        "hjp",
        "hna",
        "harga",
        "whse",
        "tanggal_expired",
        "batch",
        "prsnd",
        "prsnpot",
        "prsnt",
        "prsnbp",
        "prsnbmp",
        "bonus",
        "facAcu",
        "kode_team",
        "team",
        "dun",
        "distribute_apks",
        "distributed_id",
        "distributed_name",
        "parent_id",
        "missing_facno",
        "no_order",
        "periode",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "kode_distributor": "string",
        "type": "string",
        "facno": "string",
        "tanggal": "string",
        "kode_produk": "string",
        "produk": "string",
        "kode_produk_oi": "string",
        "produk_oi": "string",
        "kode_group_produk": "string",
        "group_produk": "string",
        "kode_subgroup_produk": "string",
        "subgroup_produk": "string",
        "kode_branch": "string",
        "branch": "string",
        "id_branch_oi": "string",
        "kode_branch_oi": "string",
        "branch_oi": "string",
        "kode_outlet": "string",
        "cust_id": "string",
        "outlet": "string",
        "alamat_outlet": "string",
        "kode_outlet_oi": "string",
        "outlet_oi": "string",
        "alamat_outlet_oi": "string",
        "kode_group_outlet": "string",
        "group_outlet": "string",
        "kode_salur": "string",
        "kode_sector": "string",
        "sector": "string",
        "kode_channel": "string",
        "channel": "string",
        "kode_sub_channel": "string",
        "sub_channel": "string",
        "kode_region": "string",
        "region": "string",
        "qty": "decimal",
        "faktor_kali": "decimal",
        "hjp": "decimal",
        "hna": "decimal",
        "harga": "decimal",
        "whse": "string",
        "tanggal_expired": "string",
        "batch": "string",
        "prsnd": "decimal",
        "prsnpot": "decimal",
        "prsnt": "decimal",
        "prsnbp": "decimal",
        "prsnbmp": "decimal",
        "bonus": "decimal",
        "facAcu": "string",
        "kode_team": "string",
        "team": "string",
        "dun": "string",
        "distribute_apks": "string",
        "distributed_id": "string",
        "distributed_name": "string",
        "parent_id": "string",
        "missing_facno": "string",
        "no_order": "string",
        "periode": "string",
    }

    column_mapping = {
        "kode_distributor": "kode_distributor",
        "type": "type",
        "facno": "facno",
        "tanggal": "tanggal",
        "kode_produk": "kode_produk",
        "produk": "produk",
        "kode_produk_oi": "kode_produk_oi",
        "produk_oi": "produk_oi",
        "kode_group_produk": "kode_group_produk",
        "group_produk": "group_produk",
        "kode_subgroup_produk": "kode_subgroup_produk",
        "subgroup_produk": "subgroup_produk",
        "kode_branch": "kode_branch",
        "branch": "branch",
        "id_branch_oi": "id_branch_oi",
        "kode_branch_oi": "kode_branch_oi",
        "branch_oi": "branch_oi",
        "kode_outlet": "kode_outlet",
        "cust_id": "cust_id",
        "outlet": "outlet",
        "alamat_outlet": "alamat_outlet",
        "kode_outlet_oi": "kode_outlet_oi",
        "outlet_oi": "outlet_oi",
        "alamat_outlet_oi": "alamat_outlet_oi",
        "kode_group_outlet": "kode_group_outlet",
        "group_outlet": "group_outlet",
        "kode_salur": "kode_salur",
        "kode_sector": "kode_sector",
        "sector": "sector",
        "kode_channel": "kode_channel",
        "channel": "channel",
        "kode_sub_channel": "kode_sub_channel",
        "sub_channel": "sub_channel",
        "kode_region": "kode_region",
        "region": "region",
        "qty": "qty",
        "faktor_kali": "faktor_kali",
        "hjp": "hjp",
        "hna": "hna",
        "harga": "harga",
        "whse": "whse",
        "tanggal_expired": "tanggal_expired",
        "batch": "batch",
        "prsnd": "prsnd",
        "prsnpot": "prsnpot",
        "prsnt": "prsnt",
        "prsnbp": "prsnbp",
        "prsnbmp": "prsnbmp",
        "bonus": "bonus",
        "facAcu": "facAcu",
        "kode_team": "kode_team",
        "team": "team",
        "dun": "dun",
        "distribute_apks": "distribute_apks",
        "distributed_id": "distributed_id",
        "distributed_name": "distributed_name",
        "parent_id": "parent_id",
        "missing_facno": "missing_facno",
        "no_order": "no_order",
        "periode": "periode",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements
        data["tanggal"] = data["tanggal"].dt.strftime("%Y%m%d")
        data["tanggal_expired"] = data["tanggal_expired"].dt.strftime("%Y%m%d")

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["tanggal"].astype(str)
            + data["kode_branch"].astype(str)
            + "-"
            + data["facno"].astype(str)
            + "-"
            + data["kode_produk"].astype(str)
            + "-"
            + data["kode_outlet"].astype(str)
            + "-"
            + data["cust_id"].astype(str)
            + "-"
            + data["qty"].astype(str)
        )

        data["name"] = (
            data["tanggal"].astype(str)
            + data["kode_branch"].astype(str)
            + "-"
            + data["facno"].astype(str)
            + "-"
            + data["kode_produk"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawAPLSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawAPLSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    kode_distributor=row.get("kode_distributor", ""),
                    type=row.get("type", ""),
                    facno=row.get("facno", ""),
                    tanggal=row.get("tanggal", ""),
                    kode_produk=row.get("kode_produk", ""),
                    produk=row.get("produk", ""),
                    kode_produk_oi=row.get("kode_produk_oi", ""),
                    produk_oi=row.get("produk_oi", ""),
                    kode_group_produk=row.get("kode_group_produk", ""),
                    group_produk=row.get("group_produk", ""),
                    kode_subgroup_produk=row.get("kode_subgroup_produk", ""),
                    subgroup_produk=row.get("subgroup_produk", ""),
                    kode_branch=row.get("kode_branch", ""),
                    branch=row.get("branch", ""),
                    id_branch_oi=row.get("id_branch_oi", ""),
                    kode_branch_oi=row.get("kode_branch_oi", ""),
                    branch_oi=row.get("branch_oi", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    cust_id=row.get("cust_id", ""),
                    outlet=row.get("outlet", ""),
                    alamat_outlet=row.get("alamat_outlet", ""),
                    kode_outlet_oi=row.get("kode_outlet_oi", ""),
                    outlet_oi=row.get("outlet_oi", ""),
                    alamat_outlet_oi=row.get("alamat_outlet_oi", ""),
                    kode_group_outlet=row.get("kode_group_outlet", ""),
                    group_outlet=row.get("group_outlet", ""),
                    kode_salur=row.get("kode_salur", ""),
                    kode_sector=row.get("kode_sector", ""),
                    sector=row.get("sector", ""),
                    kode_channel=row.get("kode_channel", ""),
                    channel=row.get("channel", ""),
                    kode_sub_channel=row.get("kode_sub_channel", ""),
                    sub_channel=row.get("sub_channel", ""),
                    kode_region=row.get("kode_region", ""),
                    region=row.get("region", ""),
                    qty=row.get("qty", 0.0),
                    faktor_kali=row.get("faktor_kali", 0.0),
                    hjp=row.get("hjp", 0.0),
                    hna=row.get("hna", 0.0),
                    harga=row.get("harga", 0.0),
                    whse=row.get("whse", ""),
                    tanggal_expired=row.get("tanggal_expired", ""),
                    batch=row.get("batch", ""),
                    prsnd=row.get("prsnd", 0.0),
                    prsnpot=row.get("prsnpot", 0.0),
                    prsnt=row.get("prsnt", 0.0),
                    prsnbp=row.get("prsnbp", 0.0),
                    prsnbmp=row.get("prsnbmp", 0.0),
                    bonus=row.get("bonus", 0.0),
                    facAcu=row.get("facAcu", ""),
                    kode_team=row.get("kode_team", ""),
                    team=row.get("team", ""),
                    dun=row.get("dun", ""),
                    distribute_apks=row.get("distribute_apks", ""),
                    distributed_id=row.get("distributed_id", ""),
                    distributed_name=row.get("distributed_name", ""),
                    parent_id=row.get("parent_id", ""),
                    missing_facno=row.get("missing_facno", ""),
                    no_order=row.get("no_order", ""),
                    periode=row.get("periode", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            RawAPLSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawAPLSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawAPLSO(
                    id=existing_code_to_id.get(row["code"]),
                    kode_distributor=row.get("kode_distributor", ""),
                    type=row.get("type", ""),
                    facno=row.get("facno", ""),
                    tanggal=row.get("tanggal", ""),
                    kode_produk=row.get("kode_produk", ""),
                    produk=row.get("produk", ""),
                    kode_produk_oi=row.get("kode_produk_oi", ""),
                    produk_oi=row.get("produk_oi", ""),
                    kode_group_produk=row.get("kode_group_produk", ""),
                    group_produk=row.get("group_produk", ""),
                    kode_subgroup_produk=row.get("kode_subgroup_produk", ""),
                    subgroup_produk=row.get("subgroup_produk", ""),
                    kode_branch=row.get("kode_branch", ""),
                    branch=row.get("branch", ""),
                    id_branch_oi=row.get("id_branch_oi", ""),
                    kode_branch_oi=row.get("kode_branch_oi", ""),
                    branch_oi=row.get("branch_oi", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    cust_id=row.get("cust_id", ""),
                    outlet=row.get("outlet", ""),
                    alamat_outlet=row.get("alamat_outlet", ""),
                    kode_outlet_oi=row.get("kode_outlet_oi", ""),
                    outlet_oi=row.get("outlet_oi", ""),
                    alamat_outlet_oi=row.get("alamat_outlet_oi", ""),
                    kode_group_outlet=row.get("kode_group_outlet", ""),
                    group_outlet=row.get("group_outlet", ""),
                    kode_salur=row.get("kode_salur", ""),
                    kode_sector=row.get("kode_sector", ""),
                    sector=row.get("sector", ""),
                    kode_channel=row.get("kode_channel", ""),
                    channel=row.get("channel", ""),
                    kode_sub_channel=row.get("kode_sub_channel", ""),
                    sub_channel=row.get("sub_channel", ""),
                    kode_region=row.get("kode_region", ""),
                    region=row.get("region", ""),
                    qty=row.get("qty", 0.0),
                    faktor_kali=row.get("faktor_kali", 0.0),
                    hjp=row.get("hjp", 0.0),
                    hna=row.get("hna", 0.0),
                    harga=row.get("harga", 0.0),
                    whse=row.get("whse", ""),
                    tanggal_expired=row.get("tanggal_expired", ""),
                    batch=row.get("batch", ""),
                    prsnd=row.get("prsnd", 0.0),
                    prsnpot=row.get("prsnpot", 0.0),
                    prsnt=row.get("prsnt", 0.0),
                    prsnbp=row.get("prsnbp", 0.0),
                    prsnbmp=row.get("prsnbmp", 0.0),
                    bonus=row.get("bonus", 0.0),
                    facAcu=row.get("facAcu", ""),
                    kode_team=row.get("kode_team", ""),
                    team=row.get("team", ""),
                    dun=row.get("dun", ""),
                    distribute_apks=row.get("distribute_apks", ""),
                    distributed_id=row.get("distributed_id", ""),
                    distributed_name=row.get("distributed_name", ""),
                    parent_id=row.get("parent_id", ""),
                    missing_facno=row.get("missing_facno", ""),
                    no_order=row.get("no_order", ""),
                    periode=row.get("periode", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawAPLSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "code",
                        "kode_distributor",
                        "type",
                        "facno",
                        "tanggal",
                        "kode_produk",
                        "produk",
                        "kode_produk_oi",
                        "produk_oi",
                        "kode_group_produk",
                        "group_produk",
                        "kode_subgroup_produk",
                        "subgroup_produk",
                        "kode_branch",
                        "branch",
                        "id_branch_oi",
                        "kode_branch_oi",
                        "branch_oi",
                        "kode_outlet",
                        "cust_id",
                        "outlet",
                        "alamat_outlet",
                        "kode_outlet_oi",
                        "outlet_oi",
                        "alamat_outlet_oi",
                        "kode_group_outlet",
                        "group_outlet",
                        "kode_salur",
                        "kode_sector",
                        "sector",
                        "kode_channel",
                        "channel",
                        "kode_sub_channel",
                        "sub_channel",
                        "kode_region",
                        "region",
                        "qty",
                        "faktor_kali",
                        "hjp",
                        "hna",
                        "harga",
                        "whse",
                        "tanggal_expired",
                        "batch",
                        "prsnd",
                        "prsnpot",
                        "prsnt",
                        "prsnbp",
                        "prsnbmp",
                        "bonus",
                        "facAcu",
                        "kode_team",
                        "team",
                        "dun",
                        "distribute_apks",
                        "distributed_id",
                        "distributed_name",
                        "parent_id",
                        "missing_facno",
                        "no_order",
                        "periode" "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RawAPPSOAdmin                                       ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering RawAPPSO in Admin Site               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/30-2025 by Noval                             ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RawAPPSO)
class RawAPPSOAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "kode_distributor",
            "type",
            "facno",
            "tanggal",
            "kode_produk",
            "produk",
            "kode_produk_oi",
            "produk_oi",
            "kode_group_produk",
            "group_produk",
            "kode_subgroup_produk",
            "subgroup_produk",
            "kode_branch",
            "branch",
            "id_branch_oi",
            "kode_branch_oi",
            "branch_oi",
            "kode_outlet",
            "cust_id",
            "outlet",
            "alamat_outlet",
            "kode_outlet_oi",
            "outlet_oi",
            "alamat_outlet_oi",
            "kode_group_outlet",
            "group_outlet",
            "kode_salur",
            "kode_sector",
            "sector",
            "kode_channel",
            "channel",
            "kode_sub_channel",
            "sub_channel",
            "kode_region",
            "region",
            "qty",
            "faktor_kali",
            "hjp",
            "hna",
            "harga",
            "whse",
            "tanggal_expired",
            "batch",
            "prsnd",
            "prsnpot",
            "prsnt",
            "prsnbp",
            "prsnbmp",
            "bonus",
            "facAcu",
            "kode_team",
            "team",
            "dun",
            "distribute_apks",
            "distributed_id",
            "distributed_name",
            "parent_id",
            "missing_facno",
            "no_order",
            "periode",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "kode_distributor",
        "type",
        "facno",
        "tanggal",
        "kode_produk",
        "produk",
        "kode_produk_oi",
        "produk_oi",
        "kode_group_produk",
        "group_produk",
        "kode_subgroup_produk",
        "subgroup_produk",
        "kode_branch",
        "branch",
        "id_branch_oi",
        "kode_branch_oi",
        "branch_oi",
        "kode_outlet",
        "cust_id",
        "outlet",
        "alamat_outlet",
        "kode_outlet_oi",
        "outlet_oi",
        "alamat_outlet_oi",
        "kode_group_outlet",
        "group_outlet",
        "kode_salur",
        "kode_sector",
        "sector",
        "kode_channel",
        "channel",
        "kode_sub_channel",
        "sub_channel",
        "kode_region",
        "region",
        "qty",
        "faktor_kali",
        "hjp",
        "hna",
        "harga",
        "whse",
        "tanggal_expired",
        "batch",
        "prsnd",
        "prsnpot",
        "prsnt",
        "prsnbp",
        "prsnbmp",
        "bonus",
        "facAcu",
        "kode_team",
        "team",
        "dun",
        "distribute_apks",
        "distributed_id",
        "distributed_name",
        "parent_id",
        "missing_facno",
        "no_order",
        "periode",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "kode_distributor": "string",
        "type": "string",
        "facno": "string",
        "tanggal": "string",
        "kode_produk": "string",
        "produk": "string",
        "kode_produk_oi": "string",
        "produk_oi": "string",
        "kode_group_produk": "string",
        "group_produk": "string",
        "kode_subgroup_produk": "string",
        "subgroup_produk": "string",
        "kode_branch": "string",
        "branch": "string",
        "id_branch_oi": "string",
        "kode_branch_oi": "string",
        "branch_oi": "string",
        "kode_outlet": "string",
        "cust_id": "string",
        "outlet": "string",
        "alamat_outlet": "string",
        "kode_outlet_oi": "string",
        "outlet_oi": "string",
        "alamat_outlet_oi": "string",
        "kode_group_outlet": "string",
        "group_outlet": "string",
        "kode_salur": "string",
        "kode_sector": "string",
        "sector": "string",
        "kode_channel": "string",
        "channel": "string",
        "kode_sub_channel": "string",
        "sub_channel": "string",
        "kode_region": "string",
        "region": "string",
        "qty": "decimal",
        "faktor_kali": "decimal",
        "hjp": "decimal",
        "hna": "decimal",
        "harga": "decimal",
        "whse": "string",
        "tanggal_expired": "string",
        "batch": "string",
        "prsnd": "decimal",
        "prsnpot": "decimal",
        "prsnt": "decimal",
        "prsnbp": "decimal",
        "prsnbmp": "decimal",
        "bonus": "decimal",
        "facAcu": "string",
        "kode_team": "string",
        "team": "string",
        "dun": "string",
        "distribute_apks": "string",
        "distributed_id": "string",
        "distributed_name": "string",
        "parent_id": "string",
        "missing_facno": "string",
        "no_order": "string",
        "periode": "string",
    }

    column_mapping = {
        "kode_distributor": "kode_distributor",
        "type": "type",
        "facno": "facno",
        "tanggal": "tanggal",
        "kode_produk": "kode_produk",
        "produk": "produk",
        "kode_produk_oi": "kode_produk_oi",
        "produk_oi": "produk_oi",
        "kode_group_produk": "kode_group_produk",
        "group_produk": "group_produk",
        "kode_subgroup_produk": "kode_subgroup_produk",
        "subgroup_produk": "subgroup_produk",
        "kode_branch": "kode_branch",
        "branch": "branch",
        "id_branch_oi": "id_branch_oi",
        "kode_branch_oi": "kode_branch_oi",
        "branch_oi": "branch_oi",
        "kode_outlet": "kode_outlet",
        "cust_id": "cust_id",
        "outlet": "outlet",
        "alamat_outlet": "alamat_outlet",
        "kode_outlet_oi": "kode_outlet_oi",
        "outlet_oi": "outlet_oi",
        "alamat_outlet_oi": "alamat_outlet_oi",
        "kode_group_outlet": "kode_group_outlet",
        "group_outlet": "group_outlet",
        "kode_salur": "kode_salur",
        "kode_sector": "kode_sector",
        "sector": "sector",
        "kode_channel": "kode_channel",
        "channel": "channel",
        "kode_sub_channel": "kode_sub_channel",
        "sub_channel": "sub_channel",
        "kode_region": "kode_region",
        "region": "region",
        "qty": "qty",
        "faktor_kali": "faktor_kali",
        "hjp": "hjp",
        "hna": "hna",
        "harga": "harga",
        "whse": "whse",
        "tanggal_expired": "tanggal_expired",
        "batch": "batch",
        "prsnd": "prsnd",
        "prsnpot": "prsnpot",
        "prsnt": "prsnt",
        "prsnbp": "prsnbp",
        "prsnbmp": "prsnbmp",
        "bonus": "bonus",
        "facAcu": "facAcu",
        "kode_team": "kode_team",
        "team": "team",
        "dun": "dun",
        "distribute_apks": "distribute_apks",
        "distributed_id": "distributed_id",
        "distributed_name": "distributed_name",
        "parent_id": "parent_id",
        "missing_facno": "missing_facno",
        "no_order": "no_order",
        "periode": "periode",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements
        data["tanggal"] = data["tanggal"].dt.strftime("%Y%m%d")
        data["tanggal_expired"] = data["tanggal_expired"].dt.strftime("%Y%m%d")

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        data[decimal_fields] = np.nan_to_num(
            data[decimal_fields].to_numpy(), nan=0.0
        ).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["tanggal"].astype(str)
            + data["kode_branch"].astype(str)
            + "-"
            + data["facno"].astype(str)
            + "-"
            + data["kode_produk"].astype(str)
            + "-"
            + data["kode_outlet"].astype(str)
            + "-"
            + data["cust_id"].astype(str)
            + "-"
            + data["qty"].astype(str)
        )

        data["name"] = (
            data["tanggal"].astype(str)
            + data["kode_branch"].astype(str)
            + "-"
            + data["facno"].astype(str)
            + "-"
            + data["kode_produk"].astype(str)
        )

        data["slug"] = (
            data["code"] + "-" + (data.groupby("code").cumcount()).astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            RawAPPSO.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                RawAPPSO(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=row.get("slug", ""),
                    kode_distributor=row.get("kode_distributor", ""),
                    type=row.get("type", ""),
                    facno=row.get("facno", ""),
                    tanggal=row.get("tanggal", ""),
                    kode_produk=row.get("kode_produk", ""),
                    produk=row.get("produk", ""),
                    kode_produk_oi=row.get("kode_produk_oi", ""),
                    produk_oi=row.get("produk_oi", ""),
                    kode_group_produk=row.get("kode_group_produk", ""),
                    group_produk=row.get("group_produk", ""),
                    kode_subgroup_produk=row.get("kode_subgroup_produk", ""),
                    subgroup_produk=row.get("subgroup_produk", ""),
                    kode_branch=row.get("kode_branch", ""),
                    branch=row.get("branch", ""),
                    id_branch_oi=row.get("id_branch_oi", ""),
                    kode_branch_oi=row.get("kode_branch_oi", ""),
                    branch_oi=row.get("branch_oi", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    cust_id=row.get("cust_id", ""),
                    outlet=row.get("outlet", ""),
                    alamat_outlet=row.get("alamat_outlet", ""),
                    kode_outlet_oi=row.get("kode_outlet_oi", ""),
                    outlet_oi=row.get("outlet_oi", ""),
                    alamat_outlet_oi=row.get("alamat_outlet_oi", ""),
                    kode_group_outlet=row.get("kode_group_outlet", ""),
                    group_outlet=row.get("group_outlet", ""),
                    kode_salur=row.get("kode_salur", ""),
                    kode_sector=row.get("kode_sector", ""),
                    sector=row.get("sector", ""),
                    kode_channel=row.get("kode_channel", ""),
                    channel=row.get("channel", ""),
                    kode_sub_channel=row.get("kode_sub_channel", ""),
                    sub_channel=row.get("sub_channel", ""),
                    kode_region=row.get("kode_region", ""),
                    region=row.get("region", ""),
                    qty=row.get("qty", 0.0),
                    faktor_kali=row.get("faktor_kali", 0.0),
                    hjp=row.get("hjp", 0.0),
                    hna=row.get("hna", 0.0),
                    harga=row.get("harga", 0.0),
                    whse=row.get("whse", ""),
                    tanggal_expired=row.get("tanggal_expired", ""),
                    batch=row.get("batch", ""),
                    prsnd=row.get("prsnd", 0.0),
                    prsnpot=row.get("prsnpot", 0.0),
                    prsnt=row.get("prsnt", 0.0),
                    prsnbp=row.get("prsnbp", 0.0),
                    prsnbmp=row.get("prsnbmp", 0.0),
                    bonus=row.get("bonus", 0.0),
                    facAcu=row.get("facAcu", ""),
                    kode_team=row.get("kode_team", ""),
                    team=row.get("team", ""),
                    dun=row.get("dun", ""),
                    distribute_apks=row.get("distribute_apks", ""),
                    distributed_id=row.get("distributed_id", ""),
                    distributed_name=row.get("distributed_name", ""),
                    parent_id=row.get("parent_id", ""),
                    missing_facno=row.get("missing_facno", ""),
                    no_order=row.get("no_order", ""),
                    periode=row.get("periode", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            RawAPPSO.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                RawAPPSO.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                RawAPPSO(
                    id=existing_code_to_id.get(row["code"]),
                    kode_distributor=row.get("kode_distributor", ""),
                    type=row.get("type", ""),
                    facno=row.get("facno", ""),
                    tanggal=row.get("tanggal", ""),
                    kode_produk=row.get("kode_produk", ""),
                    produk=row.get("produk", ""),
                    kode_produk_oi=row.get("kode_produk_oi", ""),
                    produk_oi=row.get("produk_oi", ""),
                    kode_group_produk=row.get("kode_group_produk", ""),
                    group_produk=row.get("group_produk", ""),
                    kode_subgroup_produk=row.get("kode_subgroup_produk", ""),
                    subgroup_produk=row.get("subgroup_produk", ""),
                    kode_branch=row.get("kode_branch", ""),
                    branch=row.get("branch", ""),
                    id_branch_oi=row.get("id_branch_oi", ""),
                    kode_branch_oi=row.get("kode_branch_oi", ""),
                    branch_oi=row.get("branch_oi", ""),
                    kode_outlet=row.get("kode_outlet", ""),
                    cust_id=row.get("cust_id", ""),
                    outlet=row.get("outlet", ""),
                    alamat_outlet=row.get("alamat_outlet", ""),
                    kode_outlet_oi=row.get("kode_outlet_oi", ""),
                    outlet_oi=row.get("outlet_oi", ""),
                    alamat_outlet_oi=row.get("alamat_outlet_oi", ""),
                    kode_group_outlet=row.get("kode_group_outlet", ""),
                    group_outlet=row.get("group_outlet", ""),
                    kode_salur=row.get("kode_salur", ""),
                    kode_sector=row.get("kode_sector", ""),
                    sector=row.get("sector", ""),
                    kode_channel=row.get("kode_channel", ""),
                    channel=row.get("channel", ""),
                    kode_sub_channel=row.get("kode_sub_channel", ""),
                    sub_channel=row.get("sub_channel", ""),
                    kode_region=row.get("kode_region", ""),
                    region=row.get("region", ""),
                    qty=row.get("qty", 0.0),
                    faktor_kali=row.get("faktor_kali", 0.0),
                    hjp=row.get("hjp", 0.0),
                    hna=row.get("hna", 0.0),
                    harga=row.get("harga", 0.0),
                    whse=row.get("whse", ""),
                    tanggal_expired=row.get("tanggal_expired", ""),
                    batch=row.get("batch", ""),
                    prsnd=row.get("prsnd", 0.0),
                    prsnpot=row.get("prsnpot", 0.0),
                    prsnt=row.get("prsnt", 0.0),
                    prsnbp=row.get("prsnbp", 0.0),
                    prsnbmp=row.get("prsnbmp", 0.0),
                    bonus=row.get("bonus", 0.0),
                    facAcu=row.get("facAcu", ""),
                    kode_team=row.get("kode_team", ""),
                    team=row.get("team", ""),
                    dun=row.get("dun", ""),
                    distribute_apks=row.get("distribute_apks", ""),
                    distributed_id=row.get("distributed_id", ""),
                    distributed_name=row.get("distributed_name", ""),
                    parent_id=row.get("parent_id", ""),
                    missing_facno=row.get("missing_facno", ""),
                    no_order=row.get("no_order", ""),
                    periode=row.get("periode", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                RawAPPSO.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "code",
                        "kode_distributor",
                        "type",
                        "facno",
                        "tanggal",
                        "kode_produk",
                        "produk",
                        "kode_produk_oi",
                        "produk_oi",
                        "kode_group_produk",
                        "group_produk",
                        "kode_subgroup_produk",
                        "subgroup_produk",
                        "kode_branch",
                        "branch",
                        "id_branch_oi",
                        "kode_branch_oi",
                        "branch_oi",
                        "kode_outlet",
                        "cust_id",
                        "outlet",
                        "alamat_outlet",
                        "kode_outlet_oi",
                        "outlet_oi",
                        "alamat_outlet_oi",
                        "kode_group_outlet",
                        "group_outlet",
                        "kode_salur",
                        "kode_sector",
                        "sector",
                        "kode_channel",
                        "channel",
                        "kode_sub_channel",
                        "sub_channel",
                        "kode_region",
                        "region",
                        "qty",
                        "faktor_kali",
                        "hjp",
                        "hna",
                        "harga",
                        "whse",
                        "tanggal_expired",
                        "batch",
                        "prsnd",
                        "prsnpot",
                        "prsnt",
                        "prsnbp",
                        "prsnbmp",
                        "bonus",
                        "facAcu",
                        "kode_team",
                        "team",
                        "dun",
                        "distribute_apks",
                        "distributed_id",
                        "distributed_name",
                        "parent_id",
                        "missing_facno",
                        "no_order",
                        "periode" "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesTypeAdmin                                      ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Sales Type in Admin Site             ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(SalesType)
class SalesTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "parent")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "parent",
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RepOfficeAdmin                                      ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering Representative Office in Admin Site  ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/29-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RepOffice)
class RepOfficeAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "type")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "type",
    )
    list_per_page = 1000
    has_pandas_import = True
    dtype_mapping = {"code": "string"}
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug", "remark"),
                "description": "System related information.",
            },
        ),
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
        extra_context["has_pandas_import"] = self.has_pandas_import
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
            if pd.isna(value) or value == "":
                return None
            return value

        for _, row in data.iterrows():
            # Handle Blank Fields
            code = handle_blank(row["code"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            initial = handle_blank(row["initial"])
            shortname = handle_blank(row["shortname"])
            type = handle_blank(row["type"])

            RepOffice.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                type=type,
                status=row["status"],
            )


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  TARGET MODULE                                             ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AnnualTargetAdmin                                   ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering AnnualTargetAdmin in Admin Site      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/1-2025 by Noval                              ║
# ║  Updates: Aug/7-2025 by Novel                              ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(AnnualTarget)
class AnnualTargetAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "date",
            "code",
            "product__name",
            "targetgroup",
            "type__name",
            "qty",
            "price",
            "value",
            "version",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "date",
        "code",
        "product__name",
        "targetgroup",
        "type__name",
        "qty",
        "price",
        "value",
        "version",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "date": "date",
        "product": "string",
        "targetgroup": "string",
        "type": "string",
        "qty": "decimal",
        "price": "decimal",
        "value": "decimal",
        "version": "decimal",
        "description": "string",
    }

    column_mapping = {
        "date": "date",
        "product": "product",
        "targetgroup": "targetgroup",
        "type": "type",
        "qty": "qty",
        "price": "price",
        "value": "value",
        "version": "version",
        "description": "description",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        # data[decimal_fields] = np.nan_to_num(data[decimal_fields].to_numpy(), nan=0.0).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )
        ## Matching Product
        product_obj = Product.objects.values("id", "code")
        product_df = pd.DataFrame(product_obj)
        product_df.rename(
            columns={"id": "product_id", "code": "product_code"}, inplace=True
        )
        data = data.merge(
            product_df, left_on="product", right_on="product_code", how="left"
        )

        ## Matching Type
        salestype_obj = SalesType.objects.values("id", "code")
        salestype_df = pd.DataFrame(salestype_obj)
        salestype_df.rename(
            columns={"id": "type_id", "code": "type_code"}, inplace=True
        )
        data = data.merge(
            salestype_df, left_on="type", right_on="type_code", how="left"
        )
        data = data.replace({np.nan: None})

        data["code"] = (
            data["date"].dt.strftime("%Y%m%d")
            + "-"
            + data["product"].astype(str)
            + "-"
            + data["type"].astype(str)
            + "-"
            + data["version"].astype(str)
        )

        data["name"] = (
            data["date"].dt.strftime("%Y%m%d")
            + "-"
            + data["product"].astype(str)
            + "-"
            + data["type"].astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            AnnualTarget.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                AnnualTarget(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=slugify(row["code"]) if "code" in row else "",
                    product_id=row.get("product_id", None),
                    targetgroup=row.get("targetgroup", None),
                    type_id=row.get("type_id", None),
                    date=row.get("date", None),
                    qty=row.get("qty", None),
                    price=row.get("price", None),
                    value=row.get("value", None),
                    version=row.get("version", 1),
                    description=row.get("description", ""),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            AnnualTarget.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                AnnualTarget.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                AnnualTarget(
                    id=existing_code_to_id.get(row["code"]),
                    product_id=row.get("product_id", None),
                    targetgroup=row.get("targetgroup", None),
                    type_id=row.get("type_id", None),
                    date=row.get("date", None),
                    qty=row.get("qty", None),
                    price=row.get("price", None),
                    value=row.get("value", None),
                    version=row.get("version", 1),
                    description=row.get("description", ""),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                AnnualTarget.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "product_id",
                        "targetgroup",
                        "type_id",
                        "date",
                        "qty",
                        "price",
                        "value",
                        "version",
                        "description",
                        "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: CycleTargetAdmin                                    ║
# ║  Type: Model                                               ║
# ║  Purpose: Registering CycleTargetAdmin in Admin Site       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/1-2025 by Noval                              ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(CycleTarget)
class CycleTargetAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "group_id",
            "subgroup_id",
            "item_id",
            "mr_id",
            "am_id",
            "rm_id",
            "month",
            "year",
            "type",
            "qty",
            "value",
            "version",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "group_id",
        "subgroup_id",
        "item_id",
        "mr_id",
        "am_id",
        "rm_id",
        "month",
        "year",
        "type",
        "qty",
        "value",
        "version",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "group_id": "decimal",
        "subgroup_id": "decimal",
        "item_id": "decimal",
        "mr_id": "decimal",
        "am_id": "decimal",
        "rm_id": "decimal",
        "month": "decimal",
        "year": "decimal",
        "type": "string",
        "qty": "decimal",
        "value": "decimal",
        "version": "decimal",
    }

    column_mapping = {
        "group_id": "group_id",
        "subgroup_id": "subgroup_id",
        "item_id": "item_id",
        "mr_id": "mr_id",
        "am_id": "am_id",
        "rm_id": "rm_id",
        "month": "month",
        "year": "year",
        "type": "type",
        "qty": "qty",
        "value": "value",
        "version": "version",
    }

    errors = []

    def get_actions(self, request):
        """Ensure deduplicate_records is included in the actions."""
        actions = super().get_actions(request)  # ✅ Get actions from MassActionMixin
        actions["deduplicate_records"] = (
            self.__class__.deduplicate_records,
            "deduplicate_records",
            "Deduplicate records",
        )
        actions = {"deduplicate_records": actions.pop("deduplicate_records")} | actions
        return actions

    def deduplicate_records(self, request, queryset):
        """Deduplicate records based on the 'code' field, keeping only the latest."""

        if (
            queryset is None
            or not isinstance(queryset, QuerySet)
            or not queryset.exists()
        ):
            self.message_user(
                request,
                "❌ No valid records selected for deduplication.",
                messages.ERROR,
            )
            return

        print(f"🚀 Deduplication started with {queryset.count()} selected records.")

        # Get only selected record IDs
        selected_ids = list(queryset.values_list("id", flat=True))

        # Ensure duplicates are checked only within selected records
        duplicates = (
            self.model.objects.filter(
                id__in=selected_ids
            )  # Filter within selected records
            .values("code")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        if not duplicates.exists():
            self.message_user(
                request, "❌ No duplicate records found.", messages.WARNING
            )
            return

        print(f"✅ Found {duplicates.count()} duplicate groups in selected records.")
        print(
            f"➡️ Duplicate groups in selection: {list(duplicates)}"
        )  # ✅ Print actual duplicate codes
        deleted_count = 0

        for duplicate in duplicates:
            code_value = duplicate["code"]
            duplicate_entries = list(
                self.model.objects.filter(code=code_value).order_by("-cat")
            )

            if len(duplicate_entries) > 1:
                records_to_delete = duplicate_entries[
                    1:
                ]  # ✅ Keep latest, delete older records

                for record in records_to_delete:
                    record.delete()

                deleted_count += len(records_to_delete)

        self.message_user(
            request,
            f"✅ Deduplicated {deleted_count} duplicate records.",
            messages.SUCCESS,
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
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def handle_data(self, value, expected_type):
        """
        Processes data correctly based on its expected type.
        - param value: The input value from the source (CSV/DBF).
        - param expected_type: The expected data type ('string', 'decimal', 'integer', 'fk').
        - return: Processed value in the correct format.
        """
        # Step 1: Handle Foreign Keys (Always return None if blank)
        if expected_type == "fk":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return None  # Convert blanks to None for FK fields
            return value  # Return as is for valid FK values

        # Step 2: Handle Numeric Fields (Integer & Decimal)
        elif expected_type in ["decimal", "integer"]:
            # Convert blanks or NaN to 0 for numbers
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return 0  # Convert empty values to 0

            # Ensure numbers are properly formatted
            try:
                if expected_type == "integer":
                    return int(
                        str(value).strip()
                    )  # Convert to integer, ensure no float values
                elif expected_type == "decimal":
                    return Decimal(str(value).strip())  # Convert to decimal safely
            except (ValueError, InvalidOperation):
                return 0  # If conversion fails, return 0

        # Step 3: Handle String Fields
        elif expected_type == "string":
            if value in [None, "", " ", "NULL", "nan", "NaN", "** NULL **", "-"] or (
                isinstance(value, float) and pd.isna(value)
            ):
                return ""  # Convert blanks to empty string

            # Convert numeric strings like "140.0" → "140"
            value_str = str(value).strip()

            if value_str.isdigit():
                return value_str  # ✅ Ensures "00062052" remains "00062052"

            if value_str.endswith(".0"):
                return value_str[:-2]  # ✅ Converts `"140.0"` → `"140"`

            return value_str

        # Step 4: Default return (should not reach here)
        return value

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]

        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def clean_text(self, value):
        """Remove non-ASCII characters from a string."""
        if isinstance(value, str):
            return re.sub(r"[^\x20-\x7E]", "", value).strip()
        return value  # Return original if not a string

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # Step 1: Process Data to meet requirements

        num_as_str_fields = []
        for field in num_as_str_fields:
            if field in data.columns:
                data[field] = (
                    data[field]
                    .astype(str)
                    .fillna("")
                    .str.strip()
                    .replace("nan", "")
                    .replace("None", "")
                    .str.replace(r"\.0$", "", regex=True)
                )
            elif not pd.api.types.is_object_dtype(data[field]):
                print(
                    f"🚨 ERROR: Column '{field}' is NOT string. Current dtype: {data[field].dtype}"
                )

        # clasify decimal and string fields
        decimal_fields = []
        string_fields = []
        for v, k in dtype_mapping.items():
            if k == "decimal":
                decimal_fields.append(v)
            if k == "string":
                string_fields.append(v)

        # Convert to NumPy array, fill NaNs with 0, and convert to float
        invalid_entries = ["", "N/A", "Null", "-", "NULL", "n/a"]
        data[decimal_fields] = data[decimal_fields].replace(invalid_entries, np.nan)
        # data[decimal_fields] = np.nan_to_num(data[decimal_fields].to_numpy(), nan=0.0).astype(np.float64)

        # Optional: Check for any values that could not be converted properly.
        for field in decimal_fields:
            # After conversion, these columns should be numeric. This check confirms no NaNs remain.
            if data[field].isnull().any():
                invalid_values = data[field][data[field].isnull()]
                print(
                    f"❌ ERROR: Column '{field}' contains NaN values: {invalid_values.tolist()}"
                )

        for col in string_fields:
            if col in data.columns:
                data[col] = (
                    data[col]
                    .astype(str)
                    .apply(self.clean_text)
                    .fillna("")
                    .str.strip()
                    .replace({"nan": "", "None": ""})
                    .str.replace(r"[^\x20-\x7E]", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                )

        data["code"] = (
            data["year"].astype(str)
            + data["month"].astype(str)
            + "-"
            + data["group_id"].astype(str)
            + "-"
            + data["subgroup_id"].astype(str)
            + "-"
            + data["item_id"].astype(str)
            + "-"
            + data["type"].astype(str)
            + "-"
            + data["version"].astype(str)
        )

        data["name"] = (
            data["year"].astype(str)
            + data["month"].astype(str)
            + "-"
            + data["group_id"].astype(str)
            + "-"
            + data["subgroup_id"].astype(str)
            + "-"
            + data["item_id"].astype(str)
        )

        # Step 2: Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            CycleTarget.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Step 3: Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 4: Bulk Insert New Records
        if not new_records.empty:
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = [
                CycleTarget(
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    slug=slugify(row["code"]) if "code" in row else "",
                    group_id=row.get("group_id", None),
                    subgroup_id=row.get("subgroup_id", None),
                    item_id=row.get("item_id", None),
                    mr_id=row.get("mr_id", None),
                    am_id=row.get("am_id", None),
                    rm_id=row.get("rm_id", None),
                    month=row.get("month", 0),
                    year=row.get("year", 0),
                    type=row.get("type", ""),
                    qty=row.get("qty", 0),
                    value=row.get("value", 0.0),
                    version=row.get("version", 0),
                    status=1,
                    cby=user_by,
                    cat=now(),
                )
                for row in new_records_dict
            ]

            CycleTarget.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                CycleTarget.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            existing_records_dict = existing_records.to_dict(orient="records")
            bulk_update_objs = [
                CycleTarget(
                    id=existing_code_to_id.get(row["code"]),
                    group_id=row.get("group_id", None),
                    subgroup_id=row.get("subgroup", None),
                    item_id=row.get("item_id", None),
                    mr_id=row.get("mr_id", None),
                    am_id=row.get("am_id", None),
                    rm_id=row.get("rm_id", None),
                    month=row.get("month", 0),
                    year=row.get("year", 0),
                    type=row.get("type", ""),
                    qty=row.get("qty", 0),
                    value=row.get("value", 0.0),
                    version=row.get("version", 0),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records_dict
                if row["code"] in existing_code_to_id  # ✅ Ensure `code` exists in DB
            ]
            if bulk_update_objs:
                CycleTarget.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "group_id",
                        "subgroup_id",
                        "item_id",
                        "mr_id",
                        "am_id",
                        "rm_id",
                        "month",
                        "year",
                        "type",
                        "qty",
                        "value",
                        "version",
                        "status",
                        "uby",
                        "uat",
                    ],
                )


# ╔════════════════════════════════════════════════════════════╗
# ║  SALES APPLICATION                                         ║
# ║  TERRITORY MODULE                                          ║
# ╚════════════════════════════════════════════════════════════╝
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesTeamAdmin                                      ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesTeam in Admin Site              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jun/17-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(SalesTeam)
class SalesTeamAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "business")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")
    ordering = ("code",)
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "business",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesRegionAdmin                                    ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesRegion in Admin Site            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/18-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(SalesRegion)
class SalesRegionAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "position",
            "business",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    ordering = ("code",)
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "position",
                    "business",
                    "description",
                    "effective",
                    "terminated",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: RegionProvinceAdmin                                 ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering RegionProvince in Admin Site         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/3-2025 by Setiadji                           ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(RegionProvince)
class RegionProvinceAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "region",
            "province",
            "description",
            "effective",
            "terminated",
            "remark",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
        "remark",
    )
    ordering = ("code",)
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "region",
                    "province",
                    "effective",
                    "terminated",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesAreaAdmin                                      ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesArea in Admin Site              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/17-2025 by Setiadji                          ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(SalesArea)
class SalesAreaAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "region",
            "repoffice",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    ordering = ("code",)
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "region",
                    "repoffice",
                    "effective",
                    "terminated",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: AreaRegencyAdmin                                    ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering AreaRegency in Admin Site            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/4-2025 by Setiadji                           ║
# ║  Updates:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(AreaRegency)
class AreaRegencyAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "area",
            "regency",
            "description",
            "effective",
            "terminated",
            "remark",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
        "remark",
    )
    ordering = ("code",)
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "area",
                    "regency",
                    "effective",
                    "terminated",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: SalesTerritoryAdmin                                 ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering SalesTerritory in Admin Site         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/18-2025 by Setiadji                          ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(SalesTerritory)
class SalesTerritoryAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "area",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "area",
                    "effective",
                    "terminated",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: TerritoryAssignmentAdmin                            ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering Territory Assignment in Admin Site   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jul/22-2025 by Setiadji                          ║
# ║  Updates:             by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(TerritoryAssignment)
class TerritoryAssignmentAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "assignment",
            "customer",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "assignment",
                    "customer",
                    "effective",
                    "terminated",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "remark", "slug"),
                "description": "System related information.",
            },
        ),
    )


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: KAMAreaAdmin                                        ║
# ║  Type: Model Admin                                         ║
# ║  Purpose: Registering KAMArea in Admin Site                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\admin.py                                 ║
# ║  Created: Jun/17-2025 by Setiadji                          ║
# ║  Updates: Jun/21-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@admin.register(KAMArea)
class KAMAreaAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "effective",
            "terminated",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "effective",
        "terminated",
    )
    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "effective",
                    "terminated",
                    "remark",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("status", "slug"),
                "description": "System related information.",
            },
        ),
    )


@admin.register(Satker)
class SatkerAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    # ╔════════════════════════════════════════════════════════════╗
    # ║  Name: SatkerAdmin                                         ║
    # ║  Type: Model Admin                                         ║
    # ║  Purpose: Registering Satker in Admin Site                 ║
    # ╟────────────────────────────────────────────────────────────╢
    # ║  Path: apps\sales\admin.py                                 ║
    # ║  Created: Aug/19-2025 by Noval                             ║
    # ║  Updates:                                                  ║
    # ╚════════════════════════════════════════════════════════════╝
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "jenis_instansi",
            "instansi",
            "satuan_kerja",
            "alamat_satuan_kerja",
            "customer__name",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "jenis_instansi",
        "instansi",
        "satuan_kerja",
        "alamat_satuan_kerja",
        "customer__name",
    )

    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "jenis_instansi",
                    "instansi",
                    "satuan_kerja",
                    "alamat_satuan_kerja",
                )
            },
        ),
        (
            "System Info",
            {
                "classes": ("collapsed",),
                "fields": ("name", "status", "slug"),
                "description": "System related information.",
            },
        ),
    )
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "jenis_instansi": "string",
        "instansi": "string",
        "satuan_kerja": "string",
        "alamat_satuan_kerja": "string",
        "customer_id": "Int64",
    }
    column_mapping = {
        "jenis_instansi": "jenis_instansi",
        "instansi": "instansi",
        "satuan_kerja": "satuan_kerja",
        "alamat_satuan_kerja": "alamat_satuan_kerja",
        "customer_id": "customer_id",
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]
        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=str)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        for col, dtype in dtype_mapping.items():
            if dtype == "date":
                data[col] = pd.to_datetime(data[col], errors="coerce")
            elif dtype == "string":
                data[col] = data[col].astype(dtype)
                data[col] = data[col].str.strip()
            else:
                data[col] = data[col].astype(dtype)

        # Prepare data
        data["name"] = (
            data["instansi"].fillna("")
            + "-"
            + data["satuan_kerja"].fillna("")
            + "-"
            + data["alamat_satuan_kerja"].fillna("")
        )
        data["name"] = data["name"].str[:225]
        data["slug"] = data["name"].apply(slugify)
        # remove duplicate
        data = data.drop_duplicates(subset=["slug"])

        # Check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        # Fetch Existing Name for Duplicate Checking (Single Query)
        existing_slugs = dict(
            Satker.objects.filter(slug__in=data["slug"].tolist()).values_list(
                "slug", "id"
            )
        )
        data["exists"] = data["slug"].isin(set(existing_slugs.keys()))

        # Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        if not new_records.empty:
            list_bulk_insert = []
            list_insert_column = list(dtype_mapping.keys()) + ["slug", "name"]
            for row in new_records[list_insert_column].to_dict(orient="records"):
                list_bulk_insert.append(Satker(**row, status=1, cby=user_by, cat=now()))

            created_obj = Satker.objects.bulk_create(
                list_bulk_insert,
                batch_size=batch_size,
            )

        if not existing_records.empty:
            list_updated_column = list(dtype_mapping.keys()) + ["slug", "name"]
            list_bulk_update = [
                Satker(
                    **row,
                    id=existing_slugs.get(row["slug"]),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records[list_updated_column].to_dict(
                    orient="records"
                )
            ]

            updated_obj = Satker.objects.bulk_update(
                list_bulk_update,
                list_updated_column + ["uat", "uby_id"],
                batch_size=batch_size,
            )


@admin.register(ECatalog)
class ECatalogAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    # ╔════════════════════════════════════════════════════════════╗
    # ║  Name: ECatalogAdmin                                       ║
    # ║  Type: Model Admin                                         ║
    # ║  Purpose: Registering ECatalog in Admin Site               ║
    # ╟────────────────────────────────────────────────────────────╢
    # ║  Path: apps\sales\admin.py                                 ║
    # ║  Created: Aug/19-2025 by Noval                             ║
    # ║  Updates:                                                  ║
    # ╚════════════════════════════════════════════════════════════╝
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "nomor_paket",
            "rup",
            "sumber_dana",
            "tahun_anggaran",
            "etalase",
            "jenis_katalog",
            "instansi_pengelola_etalase",
            "nama_paket",
            "jenis_instansi",
            "instansi",
            "satuan_kerja",
            "alamat_satuan_kerja",
            "nama_ppk",
            "nama_kategori",
            "merek_manufaktur",
            "nomor_produk",
            "nomor_produk_penyedia",
            "product__name",
            "nama_produk",
            "jenis_produk",
            "tkdn",
            "kuantitas_pembelian",
            "harga_satuan_pembelian",
            "ongkos_kirim",
            "total_harga",
            "tanggal_pembuatan_paket",
            "penyedia",
            "distributor",
            "status_paket",
            "deskripsi_paket",
            "status_ukm",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 3000
    has_pandas_import = True

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "nomor_paket",
        "rup",
        "sumber_dana",
        "tahun_anggaran",
        "etalase",
        "jenis_katalog",
        "instansi_pengelola_etalase",
        "nama_paket",
        "jenis_instansi",
        "instansi",
        "satuan_kerja",
        "alamat_satuan_kerja",
        "nama_ppk",
        "nama_kategori",
        "merek_manufaktur",
        "nomor_produk",
        "nomor_produk_penyedia",
        "nama_produk",
        "jenis_produk",
        "tkdn",
        "kuantitas_pembelian",
        "harga_satuan_pembelian",
        "ongkos_kirim",
        "total_harga",
        "tanggal_pembuatan_paket",
        "penyedia",
        "distributor",
        "status_paket",
        "deskripsi_paket",
        "status_ukm",
    )

    fields = None
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "nomor_paket": "string",
        "rup": "string",
        "sumber_dana": "string",
        "tahun_anggaran": "string",
        "etalase": "string",
        "jenis_katalog": "string",
        "instansi_pengelola_etalase": "string",
        "nama_paket": "string",
        "jenis_instansi": "string",
        "instansi": "string",
        "satuan_kerja": "string",
        "alamat_satuan_kerja": "string",
        "nama_ppk": "string",
        "nama_kategori": "string",
        "merek_manufaktur": "string",
        "nomor_produk": "string",
        "nomor_produk_penyedia": "string",
        "nama_produk": "string",
        "jenis_produk": "string",
        "tkdn": "string",
        "kuantitas_pembelian": "string",
        "harga_satuan_pembelian": "string",
        "ongkos_kirim": "float64",
        "total_harga": "float64",
        "tanggal_pembuatan_paket": "date",
        "penyedia": "string",
        "distributor": "string",
        "status_paket": "string",
        "deskripsi_paket": "string",
        "status_ukm": "string",
    }

    column_mapping = {
        "nomor_paket": "nomor_paket",
        "rup": "rup",
        "sumber_dana": "sumber_dana",
        "tahun_anggaran": "tahun_anggaran",
        "etalase": "etalase",
        "jenis_katalog": "jenis_katalog",
        "instansi_pengelola_etalase": "instansi_pengelola_etalase",
        "nama_paket": "nama_paket",
        "jenis_instansi": "jenis_instansi",
        "instansi": "instansi",
        "satuan_kerja": "satuan_kerja",
        "alamat_satuan_kerja": "alamat_satuan_kerja",
        "nama_ppk": "nama_ppk",
        "nama_kategori": "nama_kategori",
        "merek_manufaktur": "merek_manufaktur",
        "nomor_produk": "nomor_produk",
        "nomor_produk_penyedia": "nomor_produk_penyedia",
        "nama_produk": "nama_produk",
        "jenis_produk": "jenis_produk",
        "tkdn": "tkdn",
        "kuantitas_pembelian": "kuantitas_pembelian",
        "harga_satuan_pembelian": "harga_satuan_pembelian",
        "ongkos_kirim": "ongkos_kirim",
        "total_harga": "total_harga",
        "tanggal_pembuatan_paket": "tanggal_pembuatan_paket",
        "penyedia": "penyedia",
        "distributor": "distributor",
        "status_paket": "status_paket",
        "deskripsi_paket": "deskripsi_paket",
        "status_ukm": "status_ukm",
    }

    def changelist_view(self, request, extra_context=None):
        """
        Add pandas import URL to the changelist view context.
        """
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def normalize_column_name(self, field):
        # remove special characters and convert to lowercase
        characters_to_remove = [" ", ".", "_", "-", "(", ")", "%", "!", '"', "'"]
        for char in characters_to_remove:
            field = field.replace(char, "")
        return field.lower()

    def fix_column_mapping(self, field_name, normalized_column_mapping):
        fix_column_mapping = {}
        for field in field_name:
            normalize_field = self.normalize_column_name(field)
            if normalize_field in normalized_column_mapping:
                fix_column_mapping[field] = normalized_column_mapping[normalize_field]
        return fix_column_mapping

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                self.message_user(request, "No file uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            data = None
            try:
                dtype_mapping = getattr(self, "dtype_mapping", {})
                column_mapping = getattr(self, "column_mapping", {})

                if file_extension == ".csv":
                    first_bytes = uploaded_file.read(1024)
                    separator = "," if b"," in first_bytes else ";"
                    uploaded_file.seek(0)
                    data = pd.read_csv(
                        uploaded_file, sep=separator, dtype=dtype_mapping
                    )

                elif file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=str)

                elif file_extension == ".dbf":
                    try:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".dbf"
                        ) as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name

                        # Auto-detect encoding before reading
                        with open(temp_file_path, "rb") as f:
                            raw_data = f.read()
                            detected_encoding = chardet.detect(raw_data)["encoding"]

                        try:
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding=detected_encoding
                            )
                        except Exception:
                            print(
                                f"⚠️ Failed with detected encoding ({detected_encoding}), retrying with 'utf-8'..."
                            )
                            dbf_table = dbfread.DBF(
                                temp_file_path, encoding="utf-8"
                            )  # Fallback to 'utf-8'

                        data = pd.DataFrame(iter(dbf_table))
                        os.remove(temp_file_path)

                    except Exception as e:
                        print(f"Error importing DBF: {e}")
                        self.message_user(
                            request, f"Error importing DBF: {e}", level="error"
                        )
                        return HttpResponseRedirect(request.path)

                else:
                    self.message_user(
                        request,
                        f"Unsupported file format: {file_extension}",
                        level="error",
                    )
                    return HttpResponseRedirect(request.path)

                if data is None:
                    self.message_user(request, "Failed to process file.", level="error")
                    return HttpResponseRedirect(request.path)

                print(f"DEBUG: Processing DataFrame with shape {data.shape}")

                if not isinstance(data, pd.DataFrame):
                    raise ValueError(
                        f"ERROR: Data is not a DataFrame! Got {type(data)} instead."
                    )

                data_columns = data.columns.tolist()
                # Normalize column name from column_mapping
                column_mapping = {
                    self.normalize_column_name(k): v for k, v in column_mapping.items()
                }
                column_mapping = self.fix_column_mapping(data_columns, column_mapping)
                # rename datafrom based on column_mapping
                data.rename(columns=column_mapping, inplace=True)
                expected_columns = list(dtype_mapping.keys())
                missing_columns = [
                    col for col in expected_columns if col not in data.columns
                ]

                if missing_columns:
                    for col in missing_columns:
                        data[col] = ""  # or `None` if it should be null
                        self.message_user(
                            request,
                            f"Missing columns in uploaded file: {', '.join(missing_columns)}",
                            level="error",
                        )
                        return HttpResponseRedirect(request.path)

                # Keep only expected columns
                data = data[expected_columns]

                # Uploaded batch data
                self.message_user(request, "Processing data...")
                response = self.process_pandas_data_batch(
                    request, data
                )  # ✅ Use batch insert

                if response and response.get("download_csv"):
                    return JsonResponse({"download_csv": True})

                self.message_user(request, "Data imported successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,  # Enable batch upload checkbox for RawMUSOAdmin only
        }
        return render(request, "admin/pandas_import.html", context)

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        # check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        for col, dtype in dtype_mapping.items():
            if dtype == "date":
                data[col] = pd.to_datetime(data[col], errors="coerce")
            elif dtype == "string":
                data[col] = data[col].astype(dtype)
                data[col] = data[col].str.strip()
            else:
                data[col] = data[col].astype(dtype)

        # Prepare data
        data["name"] = data["nomor_produk_penyedia"]
        data["code"] = data["nomor_paket"] + "-" + data["nomor_produk_penyedia"]
        data["slug"] = data["code"].apply(slugify)
        data["satker_ref"] = (
            data["instansi"].fillna("")
            + "-"
            + data["satuan_kerja"].fillna("")
            + "-"
            + data["alamat_satuan_kerja"].fillna("")
        )
        data["satker_ref"] = data["satker_ref"].str[:225].apply(slugify)

        ### Matching to MfgItem (progress)
        mfgitem_obj = ManufacturingItem.objects.values("code", "product_id")
        mfgitem_df = pd.DataFrame(mfgitem_obj)
        mfgitem_df.rename(
            columns={"code": "mfgitem_code", "product_id": "mfgitem_product_id"},
            inplace=True,
        )
        data = pd.merge(
            data,
            mfgitem_df,
            how="left",
            left_on="nomor_produk_penyedia",
            right_on="mfgitem_code",
        )

        ### Matching to DistributorItem
        distitem_obj = DistributorItem.objects.values("code", "product_id")
        distitem_df = pd.DataFrame(distitem_obj)
        distitem_df.rename(
            columns={"code": "distitem_code", "product_id": "distitem_product_id"},
            inplace=True,
        )
        data = pd.merge(
            data,
            distitem_df,
            how="left",
            left_on="nomor_produk_penyedia",
            right_on="distitem_code",
        )

        ### Select match value for product_id
        data["product_id"] = (
            data["mfgitem_product_id"]
            .fillna(data["distitem_product_id"])
            .astype("Int64")
        )

        ### Matching to Product
        product_obj = Product.objects.values("id", "business_id")
        product_df = pd.DataFrame(product_obj)
        product_df.rename(columns={"id": "df_product_id"}, inplace=True)
        data = pd.merge(
            data, product_df, how="left", left_on="product_id", right_on="df_product_id"
        )

        ### Matching to Satker
        satker_obj = Satker.objects.values("id", "slug", "customer_id")
        satker_df = pd.DataFrame(satker_obj)
        satker_df.rename(
            columns={"id": "satker_id", "slug": "satker_slug"}, inplace=True
        )
        data = pd.merge(
            data, satker_df, how="left", left_on="satker_ref", right_on="satker_slug"
        )
        data = data.replace({np.nan: None})

        try:
            ## Tuncate ecatalog table
            ECatalog.objects.all().delete()
            ## Insert to ecatalog
            list_bulk_insert = []
            list_insert_column = list(dtype_mapping.keys()) + [
                "product_id",
                "business_id",
                "customer_id",
                "satker_id",
                "slug",
                "code",
                "name",
            ]
            for row in data[list_insert_column].to_dict(orient="records"):
                list_bulk_insert.append(
                    ECatalog(**row, status=1, cby=user_by, cat=now())
                )

            created_obj = ECatalog.objects.bulk_create(
                list_bulk_insert,
                batch_size=batch_size,
            )
        except Exception as e:
            raise ValueError(f"Failed insert records to ECatalog : {e}")

        ####### Insert not found satker to satker model #############################
        try:
            satker_columns = [
                "jenis_instansi",
                "instansi",
                "satuan_kerja",
                "alamat_satuan_kerja",
            ]
            df_satker = data[data["customer_id"].isna()][satker_columns]
            df_satker["name"] = (
                df_satker["instansi"].fillna("")
                + "-"
                + df_satker["satuan_kerja"].fillna("")
                + "-"
                + df_satker["alamat_satuan_kerja"].fillna("")
            )
            df_satker["name"] = df_satker["name"].str[:225]
            df_satker["slug"] = df_satker["name"].apply(slugify)
            df_satker = df_satker.drop_duplicates(subset=["slug"])
            # Fetch Existing Name for Duplicate Checking (Single Query)
            existing_slugs = dict(
                Satker.objects.filter(slug__in=df_satker["slug"].tolist()).values_list(
                    "slug", "id"
                )
            )
            df_satker["exists"] = df_satker["slug"].isin(set(existing_slugs.keys()))

            # Split into Updates & Inserts
            satker_existing_records = df_satker[df_satker["exists"]]
            satker_new_records = df_satker[~df_satker["exists"]]

            if not satker_new_records.empty:
                satker_list_bulk_insert = []
                satker_list_updated_column = satker_columns + ["slug", "name"]
                for row in satker_new_records[satker_list_updated_column].to_dict(
                    orient="records"
                ):
                    satker_list_bulk_insert.append(
                        Satker(**row, status=1, cby=user_by, cat=now())
                    )

                created_obj = Satker.objects.bulk_create(
                    satker_list_bulk_insert,
                    batch_size=batch_size,
                )

            if not satker_existing_records.empty:
                satker_list_updated_column = satker_columns + ["slug", "name"]
                satker_list_bulk_update = [
                    Satker(
                        **row,
                        id=existing_slugs.get(row["slug"]),
                        status=1,
                        uby=user_by,
                        uat=now(),
                    )
                    for row in satker_existing_records[
                        satker_list_updated_column
                    ].to_dict(orient="records")
                ]

                updated_obj = Satker.objects.bulk_update(
                    satker_list_bulk_update,
                    satker_list_updated_column + ["uat", "uby_id"],
                    batch_size=batch_size,
                )

        except Exception as e:
            raise ValueError(f"Failed insert records to Satker : {e}")
