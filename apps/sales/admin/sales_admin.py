from django.contrib import admin
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin, register_if_not_registered
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
from apps.sales.models.sales_models import (
    SalesType,
    RepOffice,
    AnnualTarget,
    CycleTarget,
    ECatalog,
)
from apps.sales.models.product_models import Product, ProductGroup, ProductSubgroup
from apps.sales.models.customer_models import Customer, Satker
from apps.humancapital.models.structure_models import Position
from apps.humancapital.models.business_models import Business

@register_if_not_registered(SalesType)
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
@register_if_not_registered(RepOffice)
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
@register_if_not_registered(AnnualTarget)
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
@register_if_not_registered(CycleTarget)
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

@register_if_not_registered(ECatalog)
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
