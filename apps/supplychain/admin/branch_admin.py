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
    Branch,
    BranchType,
    Distributor,
)

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


