from django.contrib import admin
from apps.supplychain.models.distributions import (
    OrderStatus,
    OrderType,
    DistributorItem,
    DistributorItemGroup,
    Branch,
    BranchType,
    Distributor,
    StDistDaily,
    BranchStock,
)
from apps.supplychain.models.manufacturing import (
    StockStatus,
    ManufacturingItem,
    ManufacturingItemSubgroup,
    ManufacturingItemGroup,
    StMfgOts,
)
from apps.supplychain.models.distrib_orders import (
    DODetail,
    PODetail,
    DOHeader,
    POHeader,
    OrderDetail,
    OrderHeader,
)
from apps.base.models.items import UoM
from apps.sales.models.product import Product
from apps.base.models.entities import Company
from django.db import models
from django.forms import TextInput, Textarea, NumberInput
from apps.base.admin_base import BaseModelAdmin, PandasImportMixin
from apps.base.admin_utils import MassActionMixin
from apps.base.filters import StatusListFilter, DeletedListFilter
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.timezone import now
from django.utils.text import slugify
import numpy as np
import os
from datetime import datetime


from django import forms
import pandas as pd
from django.shortcuts import redirect, render
from django.urls import reverse, path
from decimal import Decimal, InvalidOperation
import tempfile
import chardet
import dbfread
import re


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(OrderHeader)
class OrderHeaderAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + (
            "get_distributor_code",
            "orderno",
            "orderdate",
            "orderdue",
            "ordertype",
            "branch",
        )
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("orderno",)
    search_fields = BaseModelAdmin.search_fields + (
        "distributor",
        "orderno",
        "orderdate",
        "orderdue",
        "ordertype",
        "branch",
    )
    fields = (
        "distributor",
        "orderno",
        "orderdate",
        "orderdue",
        "ordertype",
        "branch",
    ) + BaseModelAdmin.fields
    autocomplete_fields = ("branch",)

    def get_distributor_code(self, obj):
        return obj.distributor.code if obj.distributor else "N/A"

    get_distributor_code.short_description = "Dist. Code"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch":
            kwargs["queryset"] = Branch.objects.filter(status=1)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(OrderDetail)
class OrderDetailAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("order", "orderline", "itemgroup", "item", "qty", "uom", "price", "amount")
        + BaseModelAdmin.list_display_name
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("item",)
    search_fields = BaseModelAdmin.search_fields + (
        "order",
        "orderline",
        "itemgroup",
        "qty",
        "uom",
        "price",
        "amount",
    )


@admin.register(StockStatus)
class StockStatusAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")


@admin.register(OrderStatus)
class OrderStatusAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")
    fields = None
    fieldsets = (
        (
            "Primary Information",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                    "progress",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "status",
                    "slug",
                    "cat",
                    "cby",
                    "uat",
                    "uby",
                    "dat",
                    "dby",
                    "deleted",
                ),
            },
        ),
    )


@admin.register(OrderType)
class OrderTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "distributor")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")
    fields = None
    fieldsets = (
        (
            "Primary Information",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "remark",
                    "distributor",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "status",
                    "slug",
                    "cat",
                    "cby",
                    "uat",
                    "uby",
                    "dat",
                    "dby",
                    "deleted",
                ),
            },
        ),
    )


@admin.register(ManufacturingItem)
class ManufacturingItemAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "subgroup",
            "owner",
            "product",
            "deliveryuom",
            "stockuom",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "name",
        "initial",
        "shortname",
    )
    list_per_page = 1000
    has_pandas_import = True
    autocomplete_fields = ("product",)
    list_select_related = ("product",)

    fields = None
    fieldsets = (
        (
            "Primary Information",
            {
                "fields": (
                    "code",
                    "name",
                    "initial",
                    "shortname",
                    "description",
                    "subgroup",
                    "owner",
                    "product",
                    "deliveryuom",
                    "stockuom",
                ),
            },
        ),
        (
            "System Information",
            {
                "fields": ("status", "remark", "slug"),
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
            owner_code = row["owner"]
            owner = None
            if pd.notna(owner_code) and owner_code.strip() != "":
                try:
                    owner = Company.objects.get(code=owner_code)
                except Company.DoesNotExist:
                    owner = None

            subgroup_code = row["subgroup"]
            subgroup = None
            if pd.notna(subgroup_code) and str(subgroup_code).strip() != "":
                try:
                    subgroup = ManufacturingItemSubgroup.objects.get(
                        code=str(subgroup_code)
                    )
                except ManufacturingItemSubgroup.DoesNotExist:
                    subgroup = None

            product_code = row["product"]
            product = None
            if pd.notna(product_code) and product_code.strip() != "":
                try:
                    product = Product.objects.get(code=product_code)
                except Product.DoesNotExist:
                    product = None

            code = handle_blank(row["code"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            initial = handle_blank(row["initial"])
            shortname = handle_blank(row["shortname"])

            ManufacturingItem.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shortname=shortname,
                subgroup=subgroup,
                owner=owner,
                product=product,
                status=row["status"],
            )


@admin.register(ManufacturingItemSubgroup)
class ManufacturingItemSubgroupAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname", "group")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "initial",
        "shortname",
        "group",
    )


@admin.register(ManufacturingItemGroup)
class ManufacturingItemGroupAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")


@admin.register(BranchStock)
class BranchStockAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + (
            "branch",
            "team",
            "product",
            "product_name",
            "trx_date",
            "total_reg",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("branch",)
    search_fields = BaseModelAdmin.search_fields + (
        "branch__code",
        "branch__name",
        "product__code",
        "product__name",
        "product_name",
    )
    list_filter = (
        DeletedListFilter,
        StatusListFilter,
        "branch",
        "team",
        "trx_date",
    )
    autocomplete_fields = ("branch", "team", "product", "group")
    date_hierarchy = "trx_date"
    list_select_related = ("branch", "team", "product", "group")
    ordering = ("-trx_date", "branch__code")

    fields = None
    prepopulated_fields = {}

    fieldsets = (
        (
            "Branch Stock Information",
            {
                "fields": (
                    "branch",
                    "product",
                    "product_name",
                    "team",
                    "group",
                    "trx_date",
                    "total_reg",
                )
            },
        ),
        (
            "System Fields",
            {
                "classes": ("collapse",),
                "fields": (
                    "name",
                    "description",
                    "remark",
                    "status",
                ),
            },
        ),
    )

    readonly_fields = ("name",)


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: DistributorItemAdmin                                  ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering DistributorItem in Admin Site          ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: by Setiadji                                        ║
# ║  Updates: Aug/05 by Setiadji                                 ║
# ╚══════════════════════════════════════════════════════════════╝
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
@admin.register(Branch)
class BranchAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + (
            "initial",
            "shortname",
            "shipto",
            "distributor",
            "type",
            "has_sales",
            "has_stock",
            "has_order",
            "address",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")
    has_pandas_import = True
    list_per_page = 1000
    ordering = ("name",)
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
                    "shipto",
                    "distributor",
                    "type",
                    "has_sales",
                    "has_stock",
                    "has_order",
                    "address",
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

            # Process Type
            type_initial = row["type"]
            type = None  # Default to None if blank
            if pd.notna(type_initial) and type_initial.strip() != "":
                try:
                    type = BranchType.objects.get(initial=type_initial)
                except BranchType.DoesNotExist:
                    type = None  # Handle as per your business logic

            # Handle Blank Fields
            code = handle_blank(row["code"])
            description = handle_blank(row["description"])
            remark = handle_blank(row["remark"])
            initial = handle_blank(row["initial"])
            shipto = handle_blank(row["shipto"])
            shortname = handle_blank(row["shortname"])
            has_sales = handle_blank(row["has_sales"])
            has_stock = handle_blank(row["has_stock"])
            has_order = handle_blank(row["has_order"])
            address = handle_blank(row["address"])

            Branch.objects.create(
                code=code,
                name=row["name"],
                description=description,
                remark=remark,
                initial=initial,
                shipto=shipto,
                shortname=shortname,
                distributor=distributor,
                type=type,
                has_sales=has_sales,
                has_stock=has_stock,
                has_order=has_order,
                address=address,
                status=row["status"],
            )


@admin.register(BranchType)
class BranchTypeAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "shortname")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "shortname")


@admin.register(Distributor)
class DistributorAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + ("code",)
        + BaseModelAdmin.list_display_name
        + ("initial", "company")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + ("code", "initial", "company")


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: StDistDaily                                           ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering StockDailyDistributor in Admin Site    ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: Jul/7 by Noval                                     ║
# ║  Updates: Jul/9 by Noval                                     ║
# ╚══════════════════════════════════════════════════════════════╝
@admin.register(StDistDaily)
class StDistDailyAdmin(MassActionMixin, BaseModelAdmin):
    list_select_related = ("branch", "distributor")

    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "kd_prod",
            "nm_prod",
            "kd_hrmn",
            "nm_hrmn",
            "kd_prc",
            "kd_cab",
            "id_cab",
            "nm_cab",
            "branch",
            "kd_io",
            "lot",
            "ed",
            "hna",
            "reg",
            "itr",
            "pp",
            "po",
            "ext",
            "dmg",
            "atr",
            "ket",
            "periode",
            "tgl_proses",
            "distributor",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "kd_prod",
        "nm_prod",
        "kd_hrmn",
        "nm_hrmn",
        "kd_prc",
        "kd_cab",
        "id_cab",
        "nm_cab",
        "branch__name",
        "kd_io",
        "lot",
        "ed",
        "hna",
        "reg",
        "itr",
        "pp",
        "po",
        "ext",
        "dmg",
        "atr",
        "ket",
        "periode",
        "tgl_proses",
        "distributor__code",
        "distributor__name",
        "distributor__initial",
        "distributor__shortname",
    )
    
# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: DODetailAdmin                                         ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering DODetail in Admin Site                 ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: Jul/14 by Noval                                    ║
# ║  Updates: Jul/17 by Noval                                    ║
# ╚══════════════════════════════════════════════════════════════╝
@admin.register(DODetail)
class DODetailAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "transaction_number",
            "dn_date",
            "dn_effdate",
            "dn",
            "shipto_code",
            "shipto_name",
            "branch_id",
            "branch__name",
            "address",
            "inv",
            "so",
            "po",
            "product_line",
            "item_number",
            "item_id",
            "item_description",
            "batch",
            "qty",
            "value_shipped",
            "uom",
            "location",
            "match_code",
            "podetail__nomor_po",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 1000
    has_pandas_import = True
    ordering = ("-dn_date",)

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "transaction_number",
        "dn_date",
        "dn_effdate",
        "dn",
        "shipto_code",
        "shipto_name",
        "address",
        "inv",
        "so",
        "po",
        "product_line",
        "item_number",
        "item_description",
        "batch",
        "qty",
        "value_shipped",
        "uom",
        "location",
        "match_code",
    )

    dtype_mapping = {
        "dn_date": "date",
        "dn_effdate": "date",
        "dn": "string",
        "shipto_code": "string",
        "shipto_name": "string",
        "address": "string",
        "inv": "string",
        "so": "string",
        "po": "string",
        "product_line": "string",
        "item_number": "string",
        "item_description": "string",
        "batch": "string",
        "qty": "int64",
        "value_shipped": "float64",
        "uom": "string",
        "location": "string",
        "transaction_number": "string",
    }

    column_mapping = {
        "DN Date": "dn_date",
        "DN EffDate": "dn_effdate",
        "DN": "dn",
        "ShipTo Code": "shipto_code",
        "ShipTo Code.1": "shipto_code_1",
        "ShipTo Name": "shipto_name",
        "Address": "address",
        "Inv": "inv",
        "SO": "so",
        "SO.1": "so_1",
        "PO": "po",
        "PO.1": "po_1",
        "Product Line": "product_line",
        "Item Number": "item_number",
        "Item Description": "item_description",
        "Batch": "batch",
        "Qty": "qty",
        "Value Shipped": "value_shipped",
        "UOM": "uom",
        "Location": "location",
        "Transaction Number": "transaction_number",
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

    def generate_match_code(self, row):
        shipto = row["so"].strip()
        if "/" not in shipto:
            shipto = shipto[2:]
            branch = row["branch_id"]
            product = row["product_id"]
            if branch and product:
                return f"{shipto}-{int(branch)}-{int(product)}"
        return None

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

                if file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=str)

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

                data.rename(columns=column_mapping, inplace=True)

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

    def extract_header(self, data, user_by):
        header_dict = dict()
        try:
            for row in data.to_dict(orient="records"):
                if row["dn"] is not None and row["dn"] != "":
                    header_dict[row["dn"]] = {
                        "dn_date": row["dn_date"],
                        "shipto_code": row["shipto_code"],
                        "shipto_name": row["shipto_name"],
                        "address": row["address"],
                        "so": row["so"],
                    }

            existing_codes = dict(
                DOHeader.objects.filter(dn__in=list(header_dict.keys())).values_list(
                    "dn", "id"
                )
            )

            list_bulk_update = []
            list_bulk_insert = []
            for key, value in header_dict.items():
                name = datetime.strftime(value["dn_date"], "%Y%m%d") + "-" + key
                if key in existing_codes:
                    list_bulk_update.append(
                        DOHeader(
                            **value,
                            id=existing_codes[key],
                            dn=key,
                            name=name,
                            slug=name.lower(),
                            uby=user_by,
                            uat=now(),
                        )
                    )
                else:
                    list_bulk_insert.append(
                        DOHeader(
                            **value,
                            dn=key,
                            name=name,
                            slug=name.lower(),
                            cby=user_by,
                            cat=now(),
                        )
                    )

            DOHeader.objects.bulk_create(list_bulk_insert, batch_size=1000)

            DOHeader.objects.bulk_update(
                list_bulk_update,
                ["dn_date", "shipto_code", "shipto_name", "address", "so"],
                batch_size=1000,
            )

            header_id_map = dict()
            for header in list_bulk_update:
                header_id_map[header.dn] = header.id
            for header in list_bulk_insert:
                header_id_map[header.dn] = header.id

            return header_id_map

        except Exception as e:
            raise ValueError(f"Failed to extract header - {e}")

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        for col, dtype in dtype_mapping.items():
            if dtype == "date":
                data[col] = pd.to_datetime(data[col], errors="coerce")
            else:
                data[col] = data[col].astype(dtype)

        ## Prepare data
        data["shipto_code"] = data["shipto_code"].fillna(data["shipto_code_1"])
        data["so"] = data["so"].fillna(data["so_1"])
        data["po"] = data["po"].fillna(data["po_1"])
        data["uom"] = data["uom"].str.strip()
        data["qty"] = -data["qty"]
        data["location"] = data["location"].str.strip()
        data["name"] = (
            data["dn_date"].dt.strftime("%Y%m%d")
            + "-"
            + data["item_number"]
            + "-"
            + data["transaction_number"]
        )
        data["code"] = data["name"]
        data["slug"] = data["name"].str.strip().str.lower()
        data["status"] = 1
        data["cby"] = user_by
        data["cat"] = now()

        ### Matching to ManufacturingItem
        mfgitem_obj = ManufacturingItem.objects.values("id", "code", "product_id")
        mfgitem_df = pd.DataFrame(mfgitem_obj)
        mfgitem_df.rename(columns={"id": "item_id", "code": "item_code"}, inplace=True)
        data = pd.merge(
            data, mfgitem_df, how="left", left_on="item_number", right_on="item_code"
        )

        ### Matching DistributorBranch
        distbranch_obj = Branch.objects.values("id", "shipto")
        distbranch_df = pd.DataFrame(distbranch_obj)
        distbranch_df = distbranch_df[
            distbranch_df["shipto"].notna() & (distbranch_df["shipto"] != "")
        ]
        distbranch_df.rename(columns={"id": "branch_id"}, inplace=True)
        # Handle shipto with have different distributor name
        distbranch_df["shipto"] = distbranch_df["shipto"].str.split("|")
        distbranch_df = distbranch_df.explode("shipto")
        distbranch_df["shipto"] = distbranch_df["shipto"].str.strip()
        # Merge to data
        data = pd.merge(
            data, distbranch_df, how="left", left_on="shipto_code", right_on="shipto"
        )

        # check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        # Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = dict(
            DODetail.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", "id"
            )
        )
        data["exists"] = data["code"].isin(set(existing_codes.keys()))

        # convert NaN value to None
        data = data.replace({np.nan: None})

        # Generate Matching Code
        data["match_code"] = data.apply(self.generate_match_code, axis=1)

        # Get PODetail
        po_objs = (
            PODetail.objects.filter(match_code__isnull=False)
            .exclude(match_code="")
            .values("id", "match_code")
        )
        po_df = pd.DataFrame(list(po_objs))

        po_df_duplicates = po_df[po_df.duplicated("match_code")]
        if not po_df_duplicates.empty:
            idx = po_df.groupby("match_code")["id"].idxmin()
            po_df = po_df.loc[idx].reset_index(drop=True)

        po_df.rename(
            columns={"id": "podetail_id", "match_code": "po_match_code"}, inplace=True
        )
        po_df["podetail_id"] = po_df["podetail_id"].astype("Int64")
        data = pd.merge(
            data, po_df, how="left", left_on="match_code", right_on="po_match_code"
        )
        data = data.replace({np.nan: None})

        # Create Header
        data.sort_values(by="transaction_number", inplace=True)
        header_id_map = self.extract_header(data, user_by)

        # Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Insert new records
        if not new_records.empty:
            list_bulk_insert = []
            list_insert_column = list(dtype_mapping.keys()) + [
                "slug",
                "code",
                "name",
                "item_id",
                "branch_id",
                "match_code",
                "podetail_id",
            ]
            for row in new_records[list_insert_column].to_dict(orient="records"):
                list_bulk_insert.append(
                    DODetail(
                        **row,
                        header_id=header_id_map.get(row["dn"], None),
                        status=1,
                        cby=user_by,
                        cat=now(),
                    )
                )

            created_obj = DODetail.objects.bulk_create(
                list_bulk_insert,
                batch_size=batch_size,
            )

        # update records
        if not existing_records.empty:
            list_updated_column = list(dtype_mapping.keys()) + [
                "slug",
                "code",
                "name",
                "item_id",
                "branch_id",
                "match_code",
                "podetail_id",
            ]
            list_bulk_update = [
                DODetail(
                    **row,
                    id=existing_codes.get(row["code"]),
                    header_id=header_id_map.get(row["dn"], None),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records[list_updated_column].to_dict(
                    orient="records"
                )
            ]

            updated_obj = DODetail.objects.bulk_update(
                list_bulk_update,
                list_updated_column + ["uat", "uby_id", "po", "header_id"],
                batch_size=batch_size,
            )


# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: PODetailAdmin                                         ║
# ║  Type: Model                                                 ║
# ║  Purpose: Registering PODetail in Admin Site                 ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\supplychain\admin.py                             ║
# ║  Created: Jul/18 by Noval                                    ║
# ║  Updates: Jul/23 by Noval                                    ║
# ╚══════════════════════════════════════════════════════════════╝
@admin.register(PODetail)
class PODetailAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "nomor_po",
            "type",
            "harmonisasi",
            "cabang",
            "branch_id",
            "ord_date",
            "due_date",
        )
        + (
            "line",
            "items",
            "item_id",
            "item_description",
            "quantity",
            "satuan",
            "hjp",
            "jumlah",
            "progress",
            "match_code",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 1000
    has_pandas_import = True
    ordering = ("name",)
    autocomplete_fields = ("item",)

    class Media:
        js = ("admin/js/order_item_autofill.js",)

    formfield_overrides = {
        models.CharField: {
            "widget": TextInput(attrs={"size": "40"})
        },  # width by characters
        models.TextField: {"widget": Textarea(attrs={"rows": 3, "cols": 40})},
        models.IntegerField: {
            "widget": NumberInput(attrs={"style": "width: 140px; text-align: right;"})
        },
        models.BigIntegerField: {
            "widget": NumberInput(attrs={"style": "width: 160px; text-align: right;"})
        },
        models.PositiveIntegerField: {
            "widget": NumberInput(attrs={"style": "width: 140px; text-align: right;"})
        },
        models.FloatField: {
            "widget": NumberInput(attrs={"style": "width: 160px; text-align: right;"})
        },
        models.DecimalField: {
            "widget": NumberInput(attrs={"style": "width: 160px; text-align: right;"})
        },
    }

    fields = None
    fieldsets = (
        (
            "Primary Info",
            {
                "fields": (
                    "code",
                    "name",
                    "nomor_po",
                    "type",
                    "harmonisasi",
                    "cabang",
                    "branch",
                    "ord_date",
                    "due_date",
                    "line",
                    "items",
                    "item",
                    "item_description",
                    "quantity",
                    "satuan",
                    "hjp",
                    "jumlah",
                    "progress",
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

    search_fields = (
        BaseModelAdmin.search_fields
        + (
            "code",
            "nomor_po",
            "type",
            "harmonisasi",
            "cabang",
            "ord_date",
            "due_date",
        )
        + (
            "line",
            "items",
            "item_description",
            "quantity",
            "satuan",
            "hjp",
            "jumlah",
            "remark",
            "match_code",
        )
    )

    dtype_mapping = {
        "nomor_po": "string",
        "type": "string",
        "harmonisasi": "string",
        "cabang": "string",
        "ord_date": "date",
        "due_date": "date",
        "line": "string",
        "items": "string",
        "item_description": "string",
        "quantity": "int64",
        "satuan": "string",
        "hjp": "float64",
        "jumlah": "float64",
        "remark": "string",
    }

    column_mapping = {
        "Nomor Po": "nomor_po",
        "Type": "type",
        "Harmonisasi": "harmonisasi",
        "Cabang": "cabang",
        "Ord Date": "ord_date",
        "Due Date": "due_date",
        "Line": "line",
        "Items": "items",
        "Item Description": "item_description",
        "Quantity": "quantity",
        "Satuan": "satuan",
        "Hjp": "hjp",
        "Jumlah": "jumlah",
        "Keterangan": "remark",
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

    def generate_match_code(self, row):
        po_no = row["nomor_po"].strip()
        branch = row["branch_id"]
        product = row["product_id"]
        if po_no and branch and product:
            return f"{po_no}-{int(branch)}-{int(product)}"
        return None

    def pandas_import(self, request):
        if request.method == "POST":
            uploaded_files = request.FILES.getlist("files")
            if not uploaded_files:
                self.message_user(request, "No files uploaded.", level="error")
                return HttpResponseRedirect(request.path)

            column_mapping = getattr(self, "column_mapping", {})

            try:
                for uploaded_file in uploaded_files:
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                    if file_extension in [".xls", ".xlsx"]:
                        df = pd.read_excel(uploaded_file, dtype=str)
                    elif file_extension == ".csv":
                        df = pd.read_csv(uploaded_file, dtype=str)
                    else:
                        self.message_user(
                            request,
                            f"Unsupported file format: {file_extension}",
                            level="error",
                        )
                        continue

                    if not isinstance(df, pd.DataFrame):
                        self.message_user(
                            request,
                            f"{uploaded_file.name} is not a valid DataFrame.",
                            level="error",
                        )
                        continue

                    df.rename(columns=column_mapping, inplace=True)

                    # Proses file
                    self.message_user(request, f"Processing file: {uploaded_file.name}")
                    response = self.process_pandas_data_batch(request, df)

                    if response and response.get("download_csv"):
                        return JsonResponse({"download_csv": True})

                self.message_user(request, "All files processed successfully.")
                return HttpResponseRedirect("..")

            except Exception as e:
                self.message_user(request, f"Error importing data: {e}", level="error")
                return HttpResponseRedirect(request.path)

        opts = self.model._meta
        context = {
            "opts": opts,
            "app_label": opts.app_label,
            "has_batch_upload": True,
        }
        return render(request, "admin/pandas_multiple_import.html", context)

    def extract_header(self, data, user_by):
        header_dict = dict()
        try:
            for row in data.to_dict(orient="records"):
                if row["nomor_po"] is not None or row["nomor_po"] != "":
                    header_dict[row["nomor_po"]] = {
                        "type": row["type"],
                        "cabang": row["cabang"],
                        "ord_date": row["ord_date"],
                        "due_date": row["due_date"],
                        "remark": row["remark"],
                    }

            existing_codes = dict(
                POHeader.objects.filter(
                    nomor_po__in=list(header_dict.keys())
                ).values_list("nomor_po", "id")
            )

            list_bulk_update = []
            list_bulk_insert = []
            for key, value in header_dict.items():
                name = datetime.strftime(value["ord_date"], "%Y%m%d") + "-" + key
                if key in existing_codes:
                    list_bulk_update.append(
                        POHeader(
                            **value,
                            id=existing_codes[key],
                            nomor_po=key,
                            name=name,
                            code=name,
                            slug=name.lower(),
                            uby=user_by,
                            uat=now(),
                        )
                    )
                else:
                    list_bulk_insert.append(
                        POHeader(
                            **value,
                            nomor_po=key,
                            name=name,
                            code=name,
                            slug=name.lower(),
                            cby=user_by,
                            cat=now(),
                        )
                    )

            POHeader.objects.bulk_create(list_bulk_insert, batch_size=1000)

            POHeader.objects.bulk_update(
                list_bulk_update,
                ["name", "code", "type", "cabang", "ord_date", "due_date", "remark"],
                batch_size=1000,
            )

            header_id_map = dict()
            for header in list_bulk_update:
                header_id_map[header.nomor_po] = header.id
            for header in list_bulk_insert:
                header_id_map[header.nomor_po] = header.id

            return header_id_map

        except Exception as e:
            raise ValueError(f"Failed to extract header - {e}")

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        ## Prepare data
        # Check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        for col, dtype in dtype_mapping.items():
            if dtype == "date":
                data[col] = pd.to_datetime(data[col], errors="coerce")
            else:
                data[col] = data[col].astype(dtype)

        ## strip every column that has string dtype
        data = data.apply(
            lambda col: (
                col.str.strip()
                if col.dtype == "object" or pd.api.types.is_string_dtype(col)
                else col
            )
        )
        data["name"] = (
            data["ord_date"].dt.strftime("%Y%m%d")
            + "-"
            + data["nomor_po"]
            + "-"
            + data["items"]
        )
        data["code"] = (
            data["ord_date"].dt.strftime("%Y%m%d")
            + "-"
            + data["nomor_po"]
            + "-"
            + data["items"]
            + "-"
            + data["harmonisasi"]
            + "-"
            + data["line"]
        )
        data["slug"] = data["code"].str.strip().str.lower()
        data["status"] = 1
        data["cby"] = user_by
        data["cat"] = now()

        ### Matching to DistributorItem
        distitem_obj = DistributorItem.objects.values(
            "id", "code", "distributor_id", "product_id"
        )
        distitem_df = pd.DataFrame(distitem_obj)
        distitem_df.rename(columns={"id": "item_id", "code": "item_code"}, inplace=True)

        # 🧼 Remove potential 1-to-many merge issues | Solve duplicate slug issue
        distitem_df = distitem_df.drop_duplicates(subset="item_code")

        data = pd.merge(
            data, distitem_df, how="left", left_on="items", right_on="item_code"
        )
        # Get first distributor_id
        if not data["distributor_id"].dropna().empty:
            nilai_default = data["distributor_id"].dropna().iloc[0]
            # Fill Nan distributor_id
            data["distributor_id"] = data["distributor_id"].fillna(nilai_default)

        ### Matching DistributorBranch
        distbranch_obj = Branch.objects.filter(status=1).values(
            "id", "initial", "distributor_id", "shipto"
        )
        distbranch_df = pd.DataFrame(distbranch_obj)
        distbranch_df = distbranch_df[
            distbranch_df["shipto"].notna() & (distbranch_df["shipto"] != "")
        ]
        distbranch_df.rename(columns={"id": "branch_id"}, inplace=True)
        distbranch_df["shipto"] = distbranch_df["shipto"].str.split("|")
        distbranch_df = distbranch_df.explode("shipto")
        distbranch_df["shipto"] = distbranch_df["shipto"].str.strip()

        # 🧼 Remove potential 1-to-many merge issues | Solve duplicate slug issue
        distbranch_df = distbranch_df.drop_duplicates(
            subset=["initial", "distributor_id"]
        )

        data = pd.merge(
            data,
            distbranch_df,
            how="left",
            left_on=["cabang", "distributor_id"],
            right_on=["initial", "distributor_id"],
        )

        # Fetch Existing Codes for Duplicate Checking (Single Query)
        existing_codes = dict(
            PODetail.objects.filter(code__in=data["code"].tolist()).values_list(
                "code", "id"
            )
        )
        data["exists"] = data["code"].isin(set(existing_codes.keys()))

        # convert NaN value to None
        data = data.replace({np.nan: None})

        # Create match_code
        data["match_code"] = data.apply(self.generate_match_code, axis=1)

        # Create Header
        header_id_map = self.extract_header(data, user_by)

        # Split into Updates & Inserts
        existing_records = data[data["exists"]]
        new_records = data[~data["exists"]]

        # Check for duplicate slugs in new_records
        dup_slugs = new_records["slug"][new_records["slug"].duplicated(keep=False)]
        if not dup_slugs.empty:
            print("⚠️ Duplicate slugs found before bulk_create:")
            print(new_records[new_records["slug"].isin(dup_slugs)])
            raise ValueError("Duplicate slugs detected in new_records.")

        # Insert new records
        if not new_records.empty:
            list_bulk_insert = []
            list_insert_column = list(dtype_mapping.keys()) + [
                "slug",
                "code",
                "name",
                "item_id",
                "branch_id",
                "match_code",
            ]
            for row in new_records[list_insert_column].to_dict(orient="records"):
                list_bulk_insert.append(
                    PODetail(
                        **row,
                        header_id=header_id_map.get(row["nomor_po"], None),
                        status=1,
                        cby=user_by,
                        cat=now(),
                    )
                )

            created_obj = PODetail.objects.bulk_create(
                list_bulk_insert,
                batch_size=batch_size,
            )

        # update records
        if not existing_records.empty:
            list_updated_column = list(dtype_mapping.keys()) + [
                "code",
                "item_id",
                "branch_id",
                "match_code",
            ]
            list_bulk_update = [
                PODetail(
                    **row,
                    id=existing_codes.get(row["code"]),
                    header_id=header_id_map.get(row["nomor_po"], None),
                    status=1,
                    uby=user_by,
                    uat=now(),
                )
                for row in existing_records[list_updated_column].to_dict(
                    orient="records"
                )
            ]

            updated_obj = PODetail.objects.bulk_update(
                list_bulk_update,
                list_updated_column + ["status", "uat", "uby_id", "header_id"],
                batch_size=batch_size,
            )


@admin.register(POHeader)
class POHeaderAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + ("code", "nomor_po", "type", "cabang", "ord_date", "due_date", "remark")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "nomor_po",
        "type",
        "cabang",
        "ord_date",
        "due_date",
        "remark",
    )


@admin.register(DOHeader)
class DOHeaderAdmin(MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + ("code", "dn_date", "dn", "shipto_code", "shipto_name", "address", "so")
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )
    list_display_links = ("name",)
    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "dn_date",
        "dn",
        "shipto_code",
        "shipto_name",
        "address",
        "so",
    )


@admin.register(StMfgOts)
class StMfgOTSAdmin(PandasImportMixin, MassActionMixin, BaseModelAdmin):
    list_display = (
        BaseModelAdmin.list_display_id
        + BaseModelAdmin.list_display_name
        + (
            "code",
            "item_number",
            "item",
            "description",
            "inv_status",
            "lot_serial",
            "palet_id",
            "location",
            "exp_date",
            "qty_oh",
            "qty_box",
            "vol_kubik",
            "berat_ton",
            "size",
            "size_um",
            "product_line",
            "stock_type",
        )
        + BaseModelAdmin.list_display_info
        + BaseModelAdmin.list_display_last
    )

    list_display_links = ("name",)
    list_per_page = 1000
    has_pandas_import = True
    ordering = ("name",)

    search_fields = BaseModelAdmin.search_fields + (
        "code",
        "item_number",
        "description",
        "inv_status",
        "lot_serial",
        "palet_id",
        "location",
        "exp_date",
        "qty_oh",
        "qty_box",
        "vol_kubik",
        "berat_ton",
        "size",
        "size_um",
        "product_line",
        "stock_type",
    )

    dtype_mapping = {
        "code": "string",
        "item_number": "string",
        "description": "string",
        "inv_status": "string",
        "lot_serial": "string",
        "palet_id": "string",
        "location": "string",
        "exp_date": "date",
        "qty_oh": "float64",
        "qty_box": "float64",
        "vol_kubik": "float64",
        "berat_ton": "float64",
        "size": "float64",
        "size_um": "string",
        "product_line": "int64",
        "stock_type": "string",
    }

    column_mapping = {
        "Item Number": "item_number",
        "Item Description": "description",
        "Item Status": "inv_status",
        "Quantity On Hand": "qty_oh",
        "Qty Box": "qty_box",
        "VOL(M3/KUBIK)": "vol_kubik",
        "BERAT (TON)": "berat_ton",
        "Batch": "lot_serial",
        "Expired": "exp_date",
        "Location": "location",
        "Product Line": "product_line",
        "Size": "size",
        "Size UM": "size_um",
        "Item Type": "stock_type",
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

                if file_extension in [".xls", ".xlsx"]:
                    data = pd.read_excel(uploaded_file, dtype=str)

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

                data.rename(columns=column_mapping, inplace=True)

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
            "has_batch_upload": True,
        }
        return render(request, "admin/pandas_import.html", context)

    def process_pandas_data_batch(self, request, data, batch_size=1000):
        user_by = request.user if request.user.is_authenticated else None
        dtype_mapping = getattr(self, "dtype_mapping", {})

        ## Prepare data
        # Check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        for col, dtype in dtype_mapping.items():
            if dtype == "date":
                data[col] = pd.to_datetime(data[col], errors="coerce")
            else:
                data[col] = data[col].astype(dtype)

        data = data.apply(
            lambda col: (
                col.str.strip()
                if col.dtype == "object" or pd.api.types.is_string_dtype(col)
                else col
            )
        )  ## strip every column that has string dtype
        data["name"] = (
            data["item_number"]
            + "-"
            + data["inv_status"]
            + "-"
            + data["lot_serial"]
            + "-"
            + data["location"]
        )
        data["code"] = (
            data["item_number"]
            + "-"
            + data["inv_status"]
            + "-"
            + data["lot_serial"]
            + "-"
            + data["location"]
        )
        data["slug"] = (
            data["code"].str.strip().str.lower()
            + "-"
            + (data.groupby("code").cumcount()).astype(str)
        )
        data["status"] = 1
        data["cby"] = user_by
        data["cat"] = now()

        ### Matching to ManufacturingItem
        mfgitem_obj = ManufacturingItem.objects.values("id", "code")
        mfgitem_df = pd.DataFrame(mfgitem_obj)
        mfgitem_df.rename(columns={"id": "item_id", "code": "item_code"}, inplace=True)
        data = pd.merge(
            data, mfgitem_df, how="left", left_on="item_number", right_on="item_code"
        )

        # Check if any column not exist
        for col in list(dtype_mapping.keys()):
            if col not in data.columns:
                data[col] = None

        # Convert NaN value to None
        data = data.replace({np.nan: None})

        # Delete Old Data
        StMfgOts.objects.all().delete()

        # Insert new records
        list_bulk_insert = []
        list_insert_column = list(dtype_mapping.keys()) + [
            "slug",
            "code",
            "name",
            "item_id",
        ]
        for row in data[list_insert_column].to_dict(orient="records"):
            list_bulk_insert.append(StMfgOts(**row, status=1, cby=user_by, cat=now()))

        created_obj = StMfgOts.objects.bulk_create(
            list_bulk_insert,
            batch_size=batch_size,
        )
