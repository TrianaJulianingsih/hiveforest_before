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
from datetime import datetime, date
import pandas as pd
import numpy as np
from django.shortcuts import redirect, render

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
from apps.supplychain.models.distrib_orders_models import (
    OrderHeader,
    OrderDetail,
    DODetail,
    PODetail,
    DOHeader,
    POHeader,
)
from apps.supplychain.models.distributions_models import (
    OrderStatus,
    OrderType,
    Distributor,
    Branch,
    DistributorItem,
    DistributorItemGroup,
)
from apps.supplychain.models.manufacturing_models import (
    StockStatus,
    ManufacturingItem,
)
from apps.base.models.items import UoM
from apps.sales.models.customer_models import Customer

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
                if pd.notna(row.get("dn")) and str(row.get("dn")).strip() != "":
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
                date_val = value.get("dn_date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y%m%d")
                elif pd.notna(date_val) and str(date_val).strip() != "":
                    try:
                        date_str = pd.to_datetime(date_val).strftime("%Y%m%d")
                    except Exception:
                        date_str = str(date_val)
                else:
                    date_str = ""

                name = f"{date_str}-{key}" if date_str else str(key)
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

            if list_bulk_insert:
                DOHeader.objects.bulk_create(list_bulk_insert, batch_size=1000)

            if list_bulk_update:
                DOHeader.objects.bulk_update(
                    list_bulk_update,
                    ["dn_date", "shipto_code", "shipto_name", "address", "so"],
                    batch_size=1000,
                )

            header_id_map = dict(
                DOHeader.objects.filter(dn__in=list(header_dict.keys())).values_list(
                    "dn", "id"
                )
            )

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
                if pd.notna(row.get("nomor_po")) and str(row.get("nomor_po")).strip() != "":
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
                date_val = value.get("ord_date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y%m%d")
                elif pd.notna(date_val) and str(date_val).strip() != "":
                    try:
                        date_str = pd.to_datetime(date_val).strftime("%Y%m%d")
                    except Exception:
                        date_str = str(date_val)
                else:
                    date_str = ""

                name = f"{date_str}-{key}" if date_str else str(key)
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

            if list_bulk_insert:
                POHeader.objects.bulk_create(list_bulk_insert, batch_size=1000)

            if list_bulk_update:
                POHeader.objects.bulk_update(
                    list_bulk_update,
                    ["name", "code", "type", "cabang", "ord_date", "due_date", "remark"],
                    batch_size=1000,
                )

            header_id_map = dict(
                POHeader.objects.filter(
                    nomor_po__in=list(header_dict.keys())
                ).values_list("nomor_po", "id")
            )

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


