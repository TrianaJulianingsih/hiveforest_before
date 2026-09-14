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
from apps.supplychain.models.distributions_models import BranchStock, Branch
from apps.sales.models.product_models import Product, ProductSubgroup, ProductGroup

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
