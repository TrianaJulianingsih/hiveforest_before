from django.forms.widgets import *
from django.forms import TextInput, Textarea
from django.db import models
from django.contrib import admin
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.filters import StatusListFilter, DeletedListFilter
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
from apps.supplychain.models.distributions_models import (
    DistributorItem,
    DistributorItemGroup,
    Distributor,
)
from apps.sales.models.product_models import Product
from apps.base.models.items import UoM

@admin.register(DistributorItem)
class DistributorItemAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "distributor",
            "product",
            "group",
            "salesuom",
            "salessize",
            "stockuom",
            "stocksize",
            "orderuom",
            "ordersize",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "name",
        "distributor__name",
        "distributor__initial",
        "product__name",
        "group__name",
    )
    list_per_page = 1000
    has_pandas_import = True
    # optional, but nice for speed:
    list_select_related = ("code", "name", "distributor")
    autocomplete_fields = ("product",)  # <-- enables search widget for Product FK
    list_select_related = ("product",)

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
                    "distributor",
                    "product",
                    "group",
                    "salesuom",
                    "salessize",
                    "stockuom",
                    "stocksize",
                    "orderuom",
                    "ordersize",
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

    list_filter = (
        DeletedListFilter,
        StatusListFilter,
    )

    dtype_mapping = {
        "code": "string",
        "name": "string",
        "description": "string",
        "remark": "string",
        "initial": "string",
        "shortname": "string",
        "group": "string",
        "distributor": "string",
        "product": "string",
        "status": "Int64",
        "salesuom": "string",
        "salessize": "Int64",
        "stockuom": "string",
        "stocksize": "Int64",
        "orderuom": "string",
        "ordersize": "Int64",
    }

    column_mapping = {
        "Code": "code",
        "Name": "name",
        "Description": "description",
        "Remark": "remark",
        "Initial": "initial",
        "Shortname": "shortname",
        "Group": "group",
        "Distributor": "distributor",
        "Product": "product",
        "Status": "status",
        "sales uom": "salesuom",
        "sales size": "salessize",
        "stock uom": "stockuom",
        "stock size": "stocksize",
        "order uom": "orderuom",
        "order size": "ordersize",
    }

    errors = []

    def changelist_view(self, request, extra_context=None):
        opts = self.model._meta
        pandas_import_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_pandas_import"
        )
        extra_context = extra_context or {}
        extra_context["has_pandas_import"] = self.has_pandas_import
        extra_context["pandas_import_url"] = pandas_import_url
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        opts = self.model._meta
        custom_urls = [
            path(
                "pandas-import/",
                self.admin_site.admin_view(self.pandas_import),  # ✅ Custom Import
                name=f"{opts.app_label}_{opts.model_name}_pandas_import",
            ),
        ]
        return custom_urls + super().get_urls()

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

                data.columns = data.columns.str.strip().str.lower()
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

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        batch = []
        total_saved = 0
        user_by = request.user if request.user.is_authenticated else None

        # data['slug'] = (data['name'] + '-' + data.groupby('name').cumcount().astype(str)).apply(slugify)
        # ✅ Generate unique slugs properly (similar to your clean() method)
        def generate_unique_slug(name, existing_slugs):
            base_slug = slugify(name)
            slug = base_slug
            counter = 1

            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1

            existing_slugs.add(slug)  # Add to set to avoid duplicates in current batch
            return slug

        def _get_str(val):
            return str(val).strip() if val is not None else ""

        # Get all existing slugs from database
        existing_slugs = set(DistributorItem.objects.values_list("slug", flat=True))

        # Generate unique slugs for the data
        data["slug"] = data["name"].apply(
            lambda name: generate_unique_slug(name, existing_slugs)
        )

        # Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = set(
            DistributorItem.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", flat=True
            )
        )
        data["exists"] = data["code"].isin(existing_codes)

        # Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Step 1: Extract unique codes from ALL records (new + existing)
        distributor_codes = (
            data["distributor"].dropna().astype(str).str.strip().unique().tolist()
        )
        product_codes = (
            data["product"].dropna().astype(str).str.strip().unique().tolist()
        )
        group_codes = data["group"].dropna().astype(str).str.strip().unique().tolist()
        salesuom_codes = (
            data["salesuom"].dropna().astype(str).str.strip().unique().tolist()
        )
        stockuom_codes = (
            data["stockuom"].dropna().astype(str).str.strip().unique().tolist()
        )
        orderuom_codes = (
            data["orderuom"].dropna().astype(str).str.strip().unique().tolist()
        )

        # Step 2: Create maps from code to instance (always available)
        distributor_map = {
            d.code: d for d in Distributor.objects.filter(code__in=distributor_codes)
        }
        product_map = {
            p.code: p for p in Product.objects.filter(code__in=product_codes)
        }
        group_map = {
            g.code: g for g in DistributorItemGroup.objects.filter(code__in=group_codes)
        }
        salesuom_map = {
            sl.code: sl for sl in UoM.objects.filter(code__in=salesuom_codes)
        }
        stockuom_map = {
            st.code: st for st in UoM.objects.filter(code__in=stockuom_codes)
        }
        orderuom_map = {
            or_.code: or_ for or_ in UoM.objects.filter(code__in=orderuom_codes)
        }

        def resolve_fks(row):
            distributor = distributor_map.get(_get_str(row.get("distributor")))
            product = product_map.get(_get_str(row.get("product")))
            group = group_map.get(_get_str(row.get("group")))
            salesuom = salesuom_map.get(_get_str(row.get("salesuom")))
            stockuom = stockuom_map.get(_get_str(row.get("stockuom")))
            orderuom = orderuom_map.get(_get_str(row.get("orderuom")))
            return distributor, product, group, salesuom, stockuom, orderuom

        def _get_num(val):
            """Convert to float/int if possible, else None."""
            if val in [None, ""]:
                return None
            try:
                return float(val)
            except ValueError:
                return None

        # Bulk Insert New Records
        if not new_records.empty:
            # Step 3: Convert records to dicts
            new_records_dict = new_records.to_dict(orient="records")
            bulk_insert_objs = []

            for row in new_records_dict:
                # Clean and lookup ForeignKeys
                distributor, product, group, salesuom, stockuom, orderuom = resolve_fks(
                    row
                )

                # Build the object
                bulk_insert_objs.append(
                    DistributorItem(
                        code=row.get("code", ""),
                        name=row.get("name", ""),
                        description=row.get("description", ""),
                        remark=row.get("remark", ""),
                        initial=row.get("initial", ""),
                        shortname=row.get("shortname", ""),
                        distributor=distributor,
                        product=product,
                        group=group,
                        salesuom=salesuom,
                        salessize=_get_num(row.get("salessize")),
                        stockuom=stockuom,
                        stocksize=_get_num(row.get("stocksize")),
                        orderuom=orderuom,
                        ordersize=_get_num(row.get("ordersize")),
                        slug=row.get("slug", ""),
                        status=1,
                        cby=user_by,
                        cat=now(),
                    )
                )

            # Step 4: Bulk create
            DistributorItem.objects.bulk_create(bulk_insert_objs, batch_size=batch_size)

        # Step 5: Bulk Update Existing Records
        if not existing_records.empty:
            existing_code_to_id = dict(
                DistributorItem.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "id")
            )
            # ✅ For updates, we need to get existing slugs for each record to avoid changing them unnecessarily
            existing_record_slugs = dict(
                DistributorItem.objects.filter(
                    code__in=existing_records["code"].tolist()
                ).values_list("code", "slug")
            )
            existing_records_dict = existing_records.to_dict(orient="records")

            bulk_update_objs = []

            for row in existing_records_dict:
                if row["code"] in existing_code_to_id:  # ✅ Ensure `code` exists in DB
                    # ✅ Keep existing slug or generate new one if name changed
                    existing_slug = existing_record_slugs.get(row["code"])
                    current_name_slug = slugify(row.get("name", ""))

                    # If the name hasn't changed significantly, keep the existing slug
                    if existing_slug and existing_slug.startswith(
                        current_name_slug.split("-")[0]
                    ):
                        final_slug = existing_slug
                    else:
                        # Generate new unique slug if name changed
                        final_slug = generate_unique_slug(
                            row.get("name", ""), existing_slugs
                        )

                    distributor, product, group, salesuom, stockuom, orderuom = (
                        resolve_fks(row)
                    )

                    bulk_update_objs.append(
                        DistributorItem(
                            id=existing_code_to_id.get(row["code"]),
                            code=row.get("code", ""),
                            name=row.get("name", ""),
                            description=row.get("description", ""),
                            remark=row.get("remark", ""),
                            initial=row.get("initial", ""),
                            shortname=row.get("shortname", ""),
                            distributor=distributor,
                            product=product,
                            group=group,
                            salesuom=salesuom,
                            salessize=_get_num(row.get("salessize")),
                            stockuom=stockuom,
                            stocksize=_get_num(row.get("stocksize")),
                            orderuom=orderuom,
                            ordersize=_get_num(row.get("ordersize")),
                            slug=final_slug,
                            status=1,
                            uby=user_by,
                            uat=now(),
                        )
                    )

            if bulk_update_objs:
                DistributorItem.objects.bulk_update(
                    bulk_update_objs,
                    [
                        "code",
                        "name",
                        "description",
                        "remark",
                        "initial",
                        "shortname",
                        "distributor",
                        "product",
                        "group",
                        "salesuom",
                        "salessize",
                        "stockuom",
                        "stocksize",
                        "orderuom",
                        "ordersize",
                        "slug",
                        "status",
                        "uby",
                        "uat",
                    ],
                    batch_size=batch_size,
                )


@admin.register(DistributorItemGroup)
class DistributorItemGroupAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
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
        "initial",
        "shortname",
        "distributor",
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
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            initial = handle_blank(row["initial"])
            shortname = handle_blank(row["shortname"])

            DistributorItemGroup.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                distributor=distributor,
                status=row["status"],
            )


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: BranchAdmin                                           ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering Branch in Admin Site                   ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: Setiadji                                           ║
# ║  Updates: Jul/16 by Setiadji                                 ║
# ╚══════════════════════════════════════════════════════════════╝
