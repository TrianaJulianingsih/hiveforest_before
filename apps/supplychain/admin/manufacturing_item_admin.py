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
from apps.supplychain.models.manufacturing_models import (
    ManufacturingItem,
    ManufacturingItemSubgroup,
    ManufacturingItemGroup,
)
from apps.sales.models.product_models import Product
from apps.base.models.entities import Company
from apps.base.models.items import UoM

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


