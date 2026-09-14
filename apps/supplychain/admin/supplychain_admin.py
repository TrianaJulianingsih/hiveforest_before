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
from apps.supplychain.models.manufacturing_models import StMfgOts, ManufacturingItem

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
