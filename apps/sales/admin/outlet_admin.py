from django.contrib import admin
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import register_if_not_registered, MassActionMixin
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
from django.urls import path, reverse
from django.utils.text import slugify
from django import forms
import pandas as pd
import numpy as np
from django.shortcuts import redirect, render

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
from apps.sales.models.customer_models import (
    Customer,
    CustomerType,
    Outlet,
    OutletGroup,
)
from apps.supplychain.models.distributions_models import Distributor, Branch

@register_if_not_registered(Outlet)
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
@register_if_not_registered(OutletGroup)
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
