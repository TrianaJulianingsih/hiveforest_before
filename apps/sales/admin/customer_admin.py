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
    CustomerGroup,
    Satker,
)
from apps.sales.models.sales_models import RepOffice
from apps.base.models.locations import Village, District, Regency, Province

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
@register_if_not_registered(Customer)
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
@register_if_not_registered(CustomerType)
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
@register_if_not_registered(CustomerGroup)
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

@register_if_not_registered(Satker)
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


